const video=document.querySelector('#video'),quality=document.querySelector('#quality'),error=document.querySelector('#error'),download=document.querySelector('#download');
const allowed=stage=>stage==='final'?[360,1080]:[360];
let variants=[];
function choose(item,keepTime=false){
 const time=keepTime?(video.currentTime||0):0,wasPlaying=keepTime&&!video.paused;
 error.hidden=true;
 video.addEventListener('loadedmetadata',()=>{if(time)video.currentTime=Math.min(time,video.duration||0);if(wasPlaying)video.play().catch(()=>{});},{once:true});
 video.src=item.src;video.load();
 download.href=item.src;download.download=item.downloadName||`geomotion-${item.height}p.mp4`;
 download.textContent=`Download ${item.height}p · ${(item.bytes/1e6).toFixed(1).replace('.',',')} MB`;
 download.hidden=false;
}
quality.addEventListener('change',()=>{const item=variants.find(v=>String(v.height)===quality.value);if(item)choose(item,true);});
video.addEventListener('error',()=>{error.textContent='Video belum berhasil dimuat. Coba ganti kualitas atau gunakan tombol download.';error.hidden=false;});
video.addEventListener('playing',()=>{error.hidden=true;});
fetch('media.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Video belum tersedia.');return r.json();}).then(media=>{
 if(!['preview','final'].includes(media.stage))throw Error('Tahap video tidak valid.');
 variants=media.variants.filter(v=>allowed(media.stage).includes(v.height));
 if(!variants.length)throw Error('Video untuk tahap ini belum tersedia.');
 document.querySelector('#stage').textContent=media.stage==='final'?'Final':'Preview · Editing';
 document.querySelector('#eyebrow').textContent=media.category||'GEOMOTION / VIDEO';
 document.querySelector('#title').textContent=media.title;document.title=media.title+' — GeoMotion';
 document.querySelector('#description').textContent=media.stage==='final'?'Versi final siap ditonton dan diunduh. Pilih kualitas yang sesuai koneksi.':'Preview komposisi dan editing. Versi 1080p dibuat setelah final diminta.';
 document.querySelector('#meta').textContent=`${media.duration.toFixed(1).replace('.',',')} detik · Vertikal 9:16`+(media.narrated?' · VO + subtitle':'');
 document.querySelector('#hint').textContent=media.stage==='final'?'Semua pilihan memakai file ringkas.':'Selama revisi, pemutar dan download tetap 360p.';
 if(media.poster)video.poster=media.poster;
 if(media.credits){document.querySelector('#credits').href=media.credits;}else document.querySelector('#credits').hidden=true;
 for(const item of variants){const option=document.createElement('option');option.value=item.height;option.textContent=`${item.height}p${item.height===360?' — hemat data':''} · ${(item.bytes/1e6).toFixed(1).replace('.',',')} MB`;quality.appendChild(option);}
 const preferred=media.stage==='preview'?360:(media.defaultQuality||1080);const initial=variants.find(v=>v.height===preferred)||variants.at(-1);
 quality.value=initial.height;quality.disabled=false;choose(initial);
}).catch(e=>{error.textContent=e.message;error.hidden=false;document.querySelector('#stage').textContent='Belum tersedia';});
