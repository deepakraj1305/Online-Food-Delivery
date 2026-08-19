document.addEventListener('DOMContentLoaded',()=>{
  document.querySelectorAll('.food-card').forEach(card=>{
    const heart=card.querySelector('.heart');
    if(heart) heart.addEventListener('click',e=>{e.preventDefault();heart.textContent=heart.textContent==='♡'?'♥':'♡';heart.classList.toggle('liked');});
  });
  setTimeout(()=>document.querySelectorAll('.flash').forEach(el=>{if(el.parentElement)el.remove()}),4500);
});
