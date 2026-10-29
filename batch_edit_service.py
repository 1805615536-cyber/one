"""Single-video local editing helper; source media is never modified."""
import cgi, json, os, shutil, subprocess, sys, time, uuid
import importlib.util
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent
def find_jianying():
    candidates=[]
    if os.environ.get('JY_EXE'): candidates.append(Path(os.environ['JY_EXE']))
    candidates.extend([Path(r'C:\Program Files\JianyingPro\JianyingPro.exe'),Path(r'C:\Program Files (x86)\JianyingPro\JianyingPro.exe')])
    for drive in ('C:', 'D:', 'E:', 'F:'):
        root=Path(drive)/'JianyingPro'
        if root.is_dir(): candidates.extend(root.glob('*/JianyingPro.exe'))
    return next((p for p in candidates if p.is_file()),None)

JY=find_jianying()
JYDIR=JY.parent if JY else Path('.')
FFMPEG=shutil.which('ffmpeg') or next((str(p) for p in (JYDIR/'ffmpeg.exe',Path(r'C:\ffmpeg\bin\ffmpeg.exe')) if p.is_file()),'ffmpeg')
FFPROBE=shutil.which('ffprobe') or next((str(p) for p in (JYDIR/'ffprobe.exe',Path(r'C:\ffmpeg\bin\ffprobe.exe')) if p.is_file()),'ffprobe')
PYTHON=sys.executable
WORK=ROOT/'work'

def probe(name, exe, args):
    if not Path(exe).exists() and not shutil.which(exe): return {'name':name,'ok':False,'detail':'未找到'}
    try:
        r=subprocess.run([exe,*args],capture_output=True,text=True,timeout=8)
        first=(r.stdout or r.stderr).splitlines()
        return {'name':name,'ok':r.returncode==0,'detail':first[0] if first else '可用'}
    except Exception as e:return {'name':name,'ok':False,'detail':str(e)}

class Handler(BaseHTTPRequestHandler):
    def send_json(self,code,obj):
        data=json.dumps(obj,ensure_ascii=False).encode();self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Access-Control-Allow-Origin','*');self.send_header('Access-Control-Allow-Headers','Content-Type');self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS');self.end_headers();self.wfile.write(data)
    def do_OPTIONS(self):self.send_json(200,{})
    def do_GET(self):
        if urlparse(self.path).path!='/api/environment':return self.send_json(404,{'error':'not found'})
        asr=importlib.util.find_spec('faster_whisper') is not None
        return self.send_json(200,{'checks':[probe('Python',PYTHON,['--version']),probe('FFmpeg',FFMPEG,['-version']),probe('FFprobe',FFPROBE,['-version']),{'name':'本地语音识别','ok':asr,'detail':'faster-whisper 已安装；首次识别会下载 small 模型' if asr else '未安装 faster-whisper'},{'name':'剪映','ok':bool(JY),'detail':str(JY) if JY else '未找到；可设置环境变量 JY_EXE 指向程序'}]})
    def do_POST(self):
        endpoint=urlparse(self.path).path
        if endpoint=='/api/transcribe':
            try:
                form=cgi.FieldStorage(fp=self.rfile,headers=self.headers,environ={'REQUEST_METHOD':'POST','CONTENT_TYPE':self.headers.get('Content-Type',''),'CONTENT_LENGTH':self.headers.get('Content-Length','0')})
                if 'audio' not in form:return self.send_json(400,{'error':'缺少演员口播音频'})
                audio=form['audio'];folder=WORK/'asr';folder.mkdir(parents=True,exist_ok=True);audio_path=folder/(uuid.uuid4().hex+'_'+Path(audio.filename).name);audio_path.write_bytes(audio.file.read())
                from faster_whisper import WhisperModel
                model=getattr(self.server,'whisper_model',None)
                if model is None:
                    model=WhisperModel('small',device='cpu',compute_type='int8');self.server.whisper_model=model
                segments,info=model.transcribe(str(audio_path),language='zh',word_timestamps=True,vad_filter=True,beam_size=5)
                rows=[]
                for seg in segments:
                    words=[{'start':round(w.start,3),'end':round(w.end,3),'text':w.word} for w in (seg.words or [])]
                    rows.append({'start':round(seg.start,3),'end':round(seg.end,3),'text':seg.text.strip(),'words':words})
                return self.send_json(200,{'language':info.language,'duration':info.duration,'segments':rows,'model':'faster-whisper-small-int8-local'})
            except ImportError:return self.send_json(503,{'error':'本地语音识别组件未安装。请先运行 setup_asr.bat。'})
            except Exception as e:return self.send_json(500,{'error':f'语音识别失败：{e}'})
        if endpoint!='/api/auto-edit':return self.send_json(404,{'error':'not found'})
        form=cgi.FieldStorage(fp=self.rfile,headers=self.headers,environ={'REQUEST_METHOD':'POST','CONTENT_TYPE':self.headers.get('Content-Type',''),'CONTENT_LENGTH':self.headers.get('Content-Length','0')})
        if 'reference' not in form:return self.send_json(400,{'error':'缺少参考视频'})
        stamp=time.strftime('%Y-%m-%d');folder=WORK/stamp/('CUT-'+time.strftime('%H%M%S')+'-'+uuid.uuid4().hex[:5]);(folder/'reference').mkdir(parents=True);(folder/'keyframes').mkdir();(folder/'assets').mkdir()
        ref=form['reference'];refname=Path(ref.filename).name;refpath=folder/'reference'/refname;refpath.write_bytes(ref.file.read())
        asset_files=form['assets'] if 'assets' in form else [];asset_files=asset_files if isinstance(asset_files,list) else [asset_files];assets=[]
        for item in asset_files:
            if not item.filename:continue
            target=folder/'assets'/Path(item.filename).name;target.write_bytes(item.file.read());assets.append({'path':str(target.resolve()),'source_name':item.filename})
        aspect=form.getfirst('aspect','9:16');script=form.getfirst('script','')
        p=subprocess.run([FFPROBE,'-v','error','-show_streams','-show_format','-of','json',str(refpath)],capture_output=True,text=True)
        if p.returncode:return self.send_json(400,{'error':'FFprobe 无法读取该视频：'+p.stderr[-400:]})
        meta=json.loads(p.stdout);fmt=meta.get('format',{});video=next((x for x in meta.get('streams',[]) if x.get('codec_type')=='video'),{});length=float(fmt.get('duration',0));fps=video.get('avg_frame_rate','0/1')
        try:num,den=map(float,fps.split('/'));rate=num/den if den else 0
        except Exception:rate=0
        # No target-duration cap. Follow the entire reference; voice/script may extend the final timeline later.
        segment=5.0;cuts=[];cursor=0.0
        while cursor<length:
            end=min(cursor+segment,length);idx=len(cuts)+1;frame=folder/'keyframes'/f'frame_{idx:03}.jpg'
            subprocess.run([FFMPEG,'-y','-ss',str(cursor+(end-cursor)/2),'-i',str(refpath),'-frames:v','1',str(frame)],capture_output=True,timeout=30)
            cuts.append({'id':f'shot_{idx:03}','start':round(cursor,3),'end':round(end,3),'duration':round(end-cursor,3),'keyframe':str(frame.resolve()),'scene_detection':'fixed_interval_pending_review'})
            cursor=end
        script_duration_estimate=round(len(''.join(script.split()))/4.0,2) if script.strip() else None
        recipe={'reference':str(refpath.resolve()),'reference_duration':length,'width':video.get('width'),'height':video.get('height'),'fps':rate,'aspect':aspect,'duration_policy':'unlimited_follow_actual_script_or_voice','script':script,'script_duration_estimate_seconds':script_duration_estimate,'target_duration':None,'shots':cuts}
        (folder/'recipe.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2),encoding='utf-8')
        matches={'assets':assets,'shots':[{'shot_id':c['id'],'asset':None,'confidence':0,'status':'缺素材：需人工匹配并确认','reason':'当前版本不伪造视觉语义匹配'} for c in cuts]}
        (folder/'matches.json').write_text(json.dumps(matches,ensure_ascii=False,indent=2),encoding='utf-8')
        (folder/'script.txt').write_text(script,encoding='utf-8')
        acceptance={'status':'待人工验收','checks':{'reference_readable':True,'keyframes_created':all(Path(c['keyframe']).exists() for c in cuts),'asset_matches_confirmed':False,'preview_created':False,'jianying_draft_validated':False}}
        (folder/'acceptance.json').write_text(json.dumps(acceptance,ensure_ascii=False,indent=2),encoding='utf-8')
        return self.send_json(200,{'message':'参考视频分析完成；已生成镜头时间表和关键帧。素材匹配与剪映草稿尚待人工确认，当前不会声称成片已完成。','artifacts':[{'name':'recipe.json','path':str((folder/'recipe.json').resolve())},{'name':'matches.json','path':str((folder/'matches.json').resolve())},{'name':'关键帧','path':str((folder/'keyframes').resolve())},{'name':'acceptance.json','path':str((folder/'acceptance.json').resolve())}],'folder':str(folder.resolve())})

if __name__=='__main__':
    WORK.mkdir(exist_ok=True)
    print('自动剪辑本机服务：http://127.0.0.1:8765')
    ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
