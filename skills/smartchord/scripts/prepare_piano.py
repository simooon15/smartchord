"""Prepare a compact, attributed Salamander v3 piano cache (macOS afconvert).
Downloads only required velocity-8 minor-third samples, never the whole library.
"""
import argparse,json,subprocess,hashlib,wave,math,base64
from pathlib import Path
from urllib.parse import quote

def fetch(url,out):
 subprocess.run(['curl','--fail','--location','--silent','--show-error','--retry','2','--output',str(out),url],check=True)
def prepare(scores,out,source):
 import numpy as np
 out=Path(out);source=Path(source);out.mkdir(parents=True,exist_ok=True);source.mkdir(parents=True,exist_ok=True)
 repo='https://github.com/sfzinstruments/SalamanderGrandPiano'
 previous=json.loads((out/'manifest.json').read_text()) if (out/'manifest.json').exists() else None
 commit_file=source/'upstream-commit.json'
 if not commit_file.exists():fetch('https://api.github.com/repos/sfzinstruments/SalamanderGrandPiano/commits/master',commit_file)
 commit=previous['commit'] if previous else json.loads(commit_file.read_text())['sha'];raw=f'https://raw.githubusercontent.com/sfzinstruments/SalamanderGrandPiano/{commit}/'
 for file in ['LICENSE','README.md']:
  if not (source/file).exists():fetch(raw+file,source/file)
 catalog={12*(o+1)+pc:f'{name}{o}v8.flac' for o in range(1,8) for pc,name in [(0,'C'),(3,'D#'),(6,'F#'),(9,'A')]}
 pitches=sorted({v[k] for score in scores for r in json.loads(Path(score).read_text())['rows'] for v in r['vocal'] if v.get('degree') for k in ['pitchBefore','pitchAfter']})
 if previous:pitches=sorted(set(pitches)|set(map(int,previous['mappings'])))
 mappings={p:min(catalog,key=lambda r:abs(r-p)) for p in pitches}
 if any(abs(p-r)>1 for p,r in mappings.items()):raise ValueError('Piano catalog outside required range')
 samples={}
 for root in sorted(set(mappings.values())):
  name=catalog[root];file=source/name
  if not file.exists():fetch(raw+'Samples/'+quote(name),file)
  if previous and str(root) in previous['samples'] and hashlib.sha256(file.read_bytes()).hexdigest()!=previous['samples'][str(root)]['sourceSha256']:raise ValueError('Piano source checksum mismatch: '+name)
  wav=source/f'{root}.wav';subprocess.run(['afconvert',str(file),str(wav),'-f','WAVE','-d','LEI16@44100','-c','1'],check=True)
  with wave.open(str(wav)) as w:sr=w.getframerate();x=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
  expected=440*2**((root-69)/12);window=x[int(.05*sr):int(.65*sr)];spectrum=np.abs(np.fft.rfft(window*np.hanning(len(window)),n=131072));lo=int(expected*.97/sr*131072);hi=int(expected*1.03/sr*131072);k=lo+int(np.argmax(spectrum[lo:hi]));a,b,c=np.log(spectrum[k-1:k+2]+1e-15);offset=(a-c)/(2*(a-2*b+c));detected=(k+offset)*sr/131072;cents=1200*math.log2(detected/expected)
  if abs(cents)>30:raise ValueError(f'Piano root {root} unexpectedly detuned {cents} cents')
  m4a=out/f'{root}.m4a';subprocess.run(['afconvert',str(wav),str(m4a),'-f','m4af','-d','aac','-b','96000','-c','1'],check=True)
  samples[str(root)]=dict(file=m4a.name,sourceFile=name,sourceSha256=hashlib.sha256(file.read_bytes()).hexdigest(),sha256=hashlib.sha256(m4a.read_bytes()).hexdigest(),duration=len(x)/sr,playbackRate=expected/detected,centsBefore=cents,peak=float(max(abs(x))))
 manifest=dict(name='Salamander Grand Piano V3',author='Alexander Holm',mappingAuthor='kinwie',license='CC BY 3.0',licenseUrl='https://creativecommons.org/licenses/by/3.0/',sourceUrl=repo,commit=commit,velocityLayer=8,sampleRate=44100,codec='AAC 96kbps mono',adaptations='Selected velocity-8 original FLAC recordings; stereo downmix to mono, resample to 44.1kHz, AAC encoding, measured root-pitch tuning; explicit nearest-root minor-third mapping (at most one semitone). No SFZ pedal/resonance/hammer-noise model.',gain=.85,mappings={str(k):v for k,v in mappings.items()},samples=samples)
 (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));(out/'LICENSE').write_bytes((source/'LICENSE').read_bytes());(out/'README.md').write_text('# Salamander Grand Piano V3\n\nAlexander Holm · CC BY 3.0. SFZ remapping repository by kinwie: '+repo+'\n\n'+manifest['adaptations']+'\n')
 print('Piano cache:',len(samples),'recorded roots;',len(pitches),'mapped pitches;',sum((out/s['file']).stat().st_size for s in samples.values()),'bytes')

def embed_piano(d,cache):
 cache=Path(cache);m=json.loads((cache/'manifest.json').read_text());pitches={v[k] for r in d['rows'] for v in r['vocal'] if v.get('degree') for k in ['pitchBefore','pitchAfter']}
 missing=pitches-set(map(int,m['mappings']))
 if missing:raise ValueError('Missing licensed piano mapping for '+str(sorted(missing)))
 roots={m['mappings'][str(p)] for p in pitches}
 for r in roots:
  info=m['samples'][str(r)];file=cache/info['file']
  if hashlib.sha256(file.read_bytes()).hexdigest()!=info['sha256']:raise ValueError('Piano cache checksum mismatch: '+str(r))
 d['pianoInfo']={**m,'mappings':{str(p):m['mappings'][str(p)] for p in sorted(pitches)},'samples':{str(r):m['samples'][str(r)] for r in sorted(roots)}};d['pianoSamples']={str(r):base64.b64encode((cache/m['samples'][str(r)]['file']).read_bytes()).decode() for r in sorted(roots)}
 d['pianoLicenseText']=(cache/'LICENSE').read_text()

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('scores',nargs='+');a.add_argument('--out',required=True);a.add_argument('--source',required=True);args=a.parse_args();prepare(args.scores,args.out,args.source)
