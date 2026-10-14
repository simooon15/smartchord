from pathlib import Path
import numpy as np,json,wave,math
import sys
P=Path(sys.argv[1]).resolve()
results=[]
for p in sorted(P.glob('*.wav'),key=lambda p:int(p.stem)):
 n=int(p.stem);f=440*2**((n-69)/12)
 with wave.open(str(p)) as w:sr=w.getframerate();x=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
 signal=x[int(.05*sr):int(.65*sr)];v=np.abs(np.fft.rfft(signal*np.hanning(len(signal)),n=131072))
 lo=int(f*.97/sr*131072);hi=int(f*1.03/sr*131072);k=lo+int(np.argmax(v[lo:hi]));a,b,c=np.log(v[k-1:k+2]+1e-15);offset=(a-c)/(2*(a-2*b+c));detected=(k+offset)*sr/131072;cents=1200*math.log2(detected/f)
 results.append({'pitch':n,'expected':f,'detected':detected,'centsBefore':cents,'playbackRate':f/detected})
(P/'tuning.json').write_text(json.dumps(results,indent=2));print('Tuning corrections:',[(r['pitch'],round(r['centsBefore'],2)) for r in results if abs(r['centsBefore'])>5]);print('Range cents',min(r['centsBefore'] for r in results),max(r['centsBefore'] for r in results))
