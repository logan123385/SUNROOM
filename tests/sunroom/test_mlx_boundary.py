"""Exercise the real worker's request boundary without loading model weights."""
import json, os, pathlib, stat, subprocess, sys, tempfile, time, unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
ROOT=pathlib.Path(__file__).resolve().parents[2]
class Boundary(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();base=pathlib.Path(cls.tmp.name)
  (base/'model').mkdir();(base/'model/config.json').write_text('{}')
  cls.ready=base/'ready.json'
  cls.proc=subprocess.Popen([sys.executable,str(ROOT/'resources/sunroom/mlx_server.py'),'--model',str(base/'model'),'--ready-file',str(cls.ready),'--parent-pid',str(os.getpid())])
  for _ in range(100):
   if cls.ready.exists():break
   time.sleep(.05)
  cls.config=json.loads(cls.ready.read_text());cls.url=f'http://127.0.0.1:{cls.config["port"]}'
 @classmethod
 def tearDownClass(cls):
  cls.proc.terminate();cls.proc.wait(timeout=5);cls.tmp.cleanup()
 def post(self,payload,authorized=True,origin=False):
  h={'Content-Type':'application/json'}
  if authorized:h['Authorization']='Bearer '+self.config['token']
  if origin:h['Origin']='https://example.invalid'
  try:
   with urlopen(Request(self.url+'/v1/chat/completions',json.dumps(payload).encode(),h),timeout=3) as r:return r.status,json.load(r)
  except HTTPError as e:return e.code,json.load(e)
 def test_private_credentials(self):
  self.assertEqual(stat.S_IMODE(self.ready.stat().st_mode),0o600)
  self.assertGreaterEqual(len(self.config['token']),40)
 def test_unauthenticated_rejected(self):self.assertEqual(self.post({},False)[0],401)
 def test_browser_rejected(self):self.assertEqual(self.post({},origin=True)[0],403)
 def test_invalid_messages_rejected(self):
  for payload in [{},{'messages':[]},{'messages':[{'role':'tool','content':'x'}]}]:self.assertEqual(self.post(payload)[0],400)
 def test_code_tools_rejected(self):
  self.assertEqual(self.post({'messages':[{'role':'user','content':'x'}],'tools':[{'name':'shell'}]})[0],400)
 def test_large_request_rejected(self):self.assertEqual(self.post({'messages':'x'*70000})[0],413)
 def test_health_does_not_load_model(self):
  with urlopen(self.url+'/health') as r:self.assertEqual(json.load(r),{'ready':True,'loaded':False})
if __name__=='__main__':unittest.main()
