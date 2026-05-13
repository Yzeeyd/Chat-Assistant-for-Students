const BASE = (location.protocol === 'http:' || location.protocol === 'https:') && location.host && !location.host.includes('localhost:0')
  ? location.origin
  : 'http://127.0.0.1:8000';
const TOKEN_KEY = 'student_assistant_token';
const LANG_KEY = 'student_assistant_lang';
const $ = (id) => document.getElementById(id);

let lang = localStorage.getItem(LANG_KEY) || 'ar';

const T = {
  ar: {
    'page.title':'المساعد الذكي للطلاب','brand.name':'جامعتي','brand.role':'مساعد الطالب الذكي',
    'auth.tagline':'جدولك ومذكراتك وخطتك الأكاديمية في مكان واحد',
    'auth.login':'تسجيل الدخول','auth.signup':'إنشاء حساب',
    'auth.email':'البريد الإلكتروني','auth.password':'كلمة المرور','auth.pass.ph':'••••••••',
    'auth.login.btn':'دخول','auth.fullname':'الاسم الكامل','auth.name.ph':'اسمك',
    'auth.pass.min':'6 أحرف على الأقل','auth.college':'الكلية','auth.college.ph':'كلية الحاسب',
    'auth.major':'التخصص','auth.major.choose':'اختر التخصص',
    'auth.major.cs':'علوم الحاسب — CS','auth.major.it':'تقنية المعلومات — IT',
    'auth.major.is':'نظم المعلومات — IS','auth.major.ce':'هندسة الحاسب — CE',
    'auth.major.se':'هندسة البرمجيات — SE','auth.major.ds':'علم البيانات — DS',
    'auth.major.ai':'الذكاء الاصطناعي — AI','auth.major.mis':'نظم المعلومات الإدارية — MIS',
    'auth.major.other':'تخصص آخر','auth.track':'المسار','auth.track.opt':'(اختياري)',
    'auth.track.ph':'مثل: شبكات، أمن معلومات','auth.signup.btn':'إنشاء الحساب',
    'nav.label':'القوائم','nav.dashboard':'لوحة التحكم','nav.chat':'المحادثة',
    'nav.schedule':'الجدول الأسبوعي','nav.reminders':'التذكيرات','nav.plan':'الخطة الأكاديمية',
    'health.connecting':'جاري الاتصال…','health.ok':'API متصل',
    'health.offline':'الخادم غير متصل','health.unavailable':'API غير متاح',
    'sidebar.clear':'حذف المحادثات','sidebar.logout':'تسجيل الخروج',
    'topbar.menu':'القائمة','topbar.theme':'تبديل المظهر','topbar.tweaks':'إعدادات المظهر',
    'dash.tagline':'تابع جدولك، تذكيراتك، وخطتك الأكاديمية. اسأل المساعد عن أي شيء — يفهم جدولك ويجاوبك بناءً عليه.',
    'dash.today':'جدول اليوم','dash.open.chat':'افتح المحادثة',
    'metric.week':'حصص الأسبوع','metric.all':'إجمالي الحصص',
    'metric.rem':'تذكيرات نشطة','metric.plan':'المتبقي بالخطة',
    'schedule.title':'جدول الأسبوع الدراسي','schedule.upload':'رفع صورة',
    'reminders.soon':'تذكيرات قريبة','reminder.add.short':'+ تذكير',
    'chat.today':'جدول اليوم','chat.all':'كل الجدول','chat.reminders':'التذكيرات',
    'chat.plan':'الخطة الأكاديمية','chat.suggest':'اقتراح مواد','chat.rules':'قواعد الجامعة',
    'chat.welcome.big':'كيف أقدر أساعدك اليوم؟',
    'chat.welcome.p':'اسأل عن جدولك أو خطتك، أضف تذكيرات، أو ارفع صورة الجدول وأنا أرتبه لك.',
    'chat.s1':'وش عندي اليوم؟','chat.s1.hint':'جدول الحصص الحالي',
    'chat.s2':'أضف تذكير','chat.s2.hint':'واجب، اختبار، موعد',
    'chat.s3':'اقتراح مواد','chat.s3.hint':'حسب خطتك الأكاديمية',
    'chat.s4':'قواعد الجامعة','chat.s4.hint':'من المستندات الرسمية',
    'chat.input.ph':'اكتب سؤالك… (Enter للإرسال، Shift+Enter لسطر جديد)',
    'chat.attach':'إرفاق صورة','chat.send':'إرسال','attach.remove':'إزالة',
    'schedule.view.title':'الجدول الأسبوعي','schedule.open.chat':'فتح بالشات',
    'schedule.upload.btn':'رفع صورة الجدول',
    'reminders.title':'التذكيرات والواجبات','reminders.add':'+ إضافة تذكير',
    'plan.title':'الخطة الأكاديمية','plan.suggest':'اقتراح مواد','plan.upload':'رفع صورة الخطة',
    'plan.active.label':'جاري الدراسة','plan.remaining.label':'المتبقية',
    'modal.room.title':'صورة المكان','modal.close':'إغلاق',
    'reminder.done':'تم ✓','reminder.ok':'حسناً',
    'tweaks.title':'إعدادات المظهر','tweaks.color':'اللون الأساسي','tweaks.density':'الكثافة',
    'tweaks.density.compact':'مدمج','tweaks.density.normal':'عادي','tweaks.density.comfort':'مريح',
    'tweaks.corners':'الزوايا','tweaks.corners.sharp':'حادة','tweaks.corners.med':'متوسطة','tweaks.corners.round':'دائرية',
    'default.student':'طالب','greet.morning':'صباح الخير','greet.evening':'مساء الخير','greet.sep':'، ',
    'room.view.btn':'عرض القاعة','schedule.empty':'لا يوجد جدول محفوظ بعد. ارفع صورة جدولك ليظهر هنا.',
    'day.classes':'حصة','day.no.classes':'لا حصص',
    'status.done':'منجز ✓','status.active':'نشط','rem.del.title':'حذف التذكير',
    'rem.empty.short':'لا توجد تذكيرات حالياً.','rem.empty.full':'لا توجد تذكيرات. أضف واحدة من المحادثة.',
    'plan.completed':'✅ مكتمل: ','plan.in.progress':'📖 جاري: ','plan.remaining':'📋 متبقي: ','plan.total':'المجموع: ',
    'plan.status.active':'قيد الدراسة','plan.status.remaining':'متبقي',
    'plan.empty':'لا توجد مواد بالخطة بعد. ارفع صورة الخطة ليتم استخراجها.',
    'import.title':'ملخص الاستيراد','import.added':'المضاف','import.skipped':'متخطى',
    'toast.logout':'تم تسجيل الخروج','toast.clear.ok':'تم حذف المحادثات',
    'toast.clear.err':'تعذر حذف المحادثات','toast.del.err':'تعذر الحذف',
    'toast.import.ok':'تم الاستيراد بنجاح ✓','toast.import.err':'فشل الاستيراد: ',
    'confirm.clear':'هل أنت متأكد أنك تريد حذف جميع المحادثات؟ لا يمكن التراجع عن هذا الإجراء.',
    'auth.signing.in':'جاري تسجيل الدخول…','auth.signing.up':'جاري إنشاء الحساب…',
    'auth.created':'تم إنشاء الحساب! سجل دخول الآن.','auth.session.expired':'انتهت الجلسة، سجل دخول من جديد',
    'uploaded.image':'رفعت صورة: ','reminder.more':'+{n} تذكيرات أخرى',
    'time.today':'اليوم ','time.tomorrow':'غداً ','locale':'ar-SA',
    'pt.dashboardView':'لوحة التحكم','pt.chatView':'المحادثة',
    'pt.scheduleView':'الجدول الأسبوعي','pt.remindersView':'التذكيرات','pt.planView':'الخطة الأكاديمية',
  },
  en: {
    'page.title':'Smart Student Assistant','brand.name':'My University','brand.role':'Smart Student Assistant',
    'auth.tagline':'Your schedule, reminders, and academic plan in one place',
    'auth.login':'Sign In','auth.signup':'Create Account',
    'auth.email':'Email','auth.password':'Password','auth.pass.ph':'••••••••',
    'auth.login.btn':'Sign In','auth.fullname':'Full Name','auth.name.ph':'Your name',
    'auth.pass.min':'At least 6 characters','auth.college':'College','auth.college.ph':'College of Computing',
    'auth.major':'Major','auth.major.choose':'Choose Major',
    'auth.major.cs':'Computer Science — CS','auth.major.it':'Information Technology — IT',
    'auth.major.is':'Information Systems — IS','auth.major.ce':'Computer Engineering — CE',
    'auth.major.se':'Software Engineering — SE','auth.major.ds':'Data Science — DS',
    'auth.major.ai':'Artificial Intelligence — AI','auth.major.mis':'Management Info Systems — MIS',
    'auth.major.other':'Other Major','auth.track':'Track','auth.track.opt':'(optional)',
    'auth.track.ph':'e.g., Networks, Cybersecurity','auth.signup.btn':'Create Account',
    'nav.label':'MENU','nav.dashboard':'Dashboard','nav.chat':'Chat',
    'nav.schedule':'Weekly Schedule','nav.reminders':'Reminders','nav.plan':'Academic Plan',
    'health.connecting':'Connecting…','health.ok':'API Connected',
    'health.offline':'Server Offline','health.unavailable':'API Unavailable',
    'sidebar.clear':'Clear Chat History','sidebar.logout':'Sign Out',
    'topbar.menu':'Menu','topbar.theme':'Toggle Theme','topbar.tweaks':'Appearance Settings',
    'dash.tagline':'Track your schedule, reminders, and academic plan. Ask the assistant anything — it knows your schedule.',
    'dash.today':"Today's Schedule",'dash.open.chat':'Open Chat',
    'metric.week':'Classes This Week','metric.all':'Total Classes',
    'metric.rem':'Active Reminders','metric.plan':'Remaining in Plan',
    'schedule.title':'Weekly Study Schedule','schedule.upload':'Upload Image',
    'reminders.soon':'Upcoming Reminders','reminder.add.short':'+ Reminder',
    'chat.today':"Today's Schedule",'chat.all':'Full Schedule','chat.reminders':'Reminders',
    'chat.plan':'Academic Plan','chat.suggest':'Suggest Courses','chat.rules':'University Rules',
    'chat.welcome.big':'How can I help you today?',
    'chat.welcome.p':"Ask about your schedule or plan, add reminders, or upload a schedule image and I'll organize it for you.",
    'chat.s1':"What's my schedule today?",'chat.s1.hint':'Current class schedule',
    'chat.s2':'Add a reminder','chat.s2.hint':'Assignment, exam, appointment',
    'chat.s3':'Suggest courses','chat.s3.hint':'Based on your academic plan',
    'chat.s4':'University rules','chat.s4.hint':'From official documents',
    'chat.input.ph':'Type your question… (Enter to send, Shift+Enter for new line)',
    'chat.attach':'Attach Image','chat.send':'Send','attach.remove':'Remove',
    'schedule.view.title':'Weekly Schedule','schedule.open.chat':'Open in Chat',
    'schedule.upload.btn':'Upload Schedule Image',
    'reminders.title':'Reminders & Assignments','reminders.add':'+ Add Reminder',
    'plan.title':'Academic Plan','plan.suggest':'Suggest Courses','plan.upload':'Upload Plan Image',
    'plan.active.label':'Currently Studying','plan.remaining.label':'Remaining',
    'modal.room.title':'Room Image','modal.close':'Close',
    'reminder.done':'Done ✓','reminder.ok':'OK',
    'tweaks.title':'Appearance Settings','tweaks.color':'Accent Color','tweaks.density':'Density',
    'tweaks.density.compact':'Compact','tweaks.density.normal':'Normal','tweaks.density.comfort':'Comfortable',
    'tweaks.corners':'Corners','tweaks.corners.sharp':'Sharp','tweaks.corners.med':'Medium','tweaks.corners.round':'Rounded',
    'default.student':'Student','greet.morning':'Good morning','greet.evening':'Good evening','greet.sep':', ',
    'room.view.btn':'View Room','schedule.empty':'No schedule saved yet. Upload your schedule image to display it here.',
    'day.classes':'class','day.no.classes':'No classes',
    'status.done':'Done ✓','status.active':'Active','rem.del.title':'Delete Reminder',
    'rem.empty.short':'No reminders yet.','rem.empty.full':'No reminders. Add one from the chat.',
    'plan.completed':'✅ Completed: ','plan.in.progress':'📖 Active: ','plan.remaining':'📋 Remaining: ','plan.total':'Total: ',
    'plan.status.active':'In Progress','plan.status.remaining':'Remaining',
    'plan.empty':'No courses in plan yet. Upload your plan image to extract them.',
    'import.title':'Import Summary','import.added':'Added','import.skipped':'Skipped',
    'toast.logout':'Signed out','toast.clear.ok':'Chat history cleared',
    'toast.clear.err':'Failed to clear chat history','toast.del.err':'Deletion failed',
    'toast.import.ok':'Successfully imported ✓','toast.import.err':'Import failed: ',
    'confirm.clear':'Are you sure you want to delete all conversations? This action cannot be undone.',
    'auth.signing.in':'Signing in…','auth.signing.up':'Creating account…',
    'auth.created':'Account created! Sign in now.','auth.session.expired':'Session expired, please sign in again',
    'uploaded.image':'Uploaded image: ','reminder.more':'+{n} more reminders',
    'time.today':'Today ','time.tomorrow':'Tomorrow ','locale':'en-US',
    'pt.dashboardView':'Dashboard','pt.chatView':'Chat',
    'pt.scheduleView':'Weekly Schedule','pt.remindersView':'Reminders','pt.planView':'Academic Plan',
  }
};

function t(key){ return (T[lang]||T.ar)[key] ?? key; }

function applyLang(){
  const isAr = lang === 'ar';
  document.documentElement.lang = lang;
  document.documentElement.dir = isAr ? 'rtl' : 'ltr';
  document.title = t('page.title');
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll('[data-i18n-ph]').forEach(el => { el.placeholder = t(el.dataset.i18nPh); });
  document.querySelectorAll('[data-i18n-aria]').forEach(el => {
    const v = t(el.dataset.i18nAria);
    el.setAttribute('aria-label', v);
    if(el.hasAttribute('title')) el.title = v;
  });
  const lb = $('langBtn'); if(lb) lb.textContent = isAr ? 'EN' : 'عر';
  renderPlan();
  renderRemindersFull();
  renderWeekGrid('weekGrid', state.lastDays);
  renderWeekGrid('weekGridFull', state.lastDays);
  const remEl = $('remListShort');
  if(remEl){
    const rems = state.lastReminders.slice(0,4);
    remEl.innerHTML = rems.length ? rems.map(rowHTML).join('') : `<div class="empty">${t('rem.empty.short')}</div>`;
  }
  $('pageTitle').textContent = t('pt.' + (document.querySelector('.view.active')?.id || 'dashboardView'));
  if(state.lastStudent?.name) renderHeader(state.lastStudent);
  const hl = $('healthLabel');
  if(hl) { const s = hl.dataset.healthState; if(s) hl.textContent = t('health.' + s); }
}
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));

const MAX_FILE_MB = 10;
const MAX_FILE_SIZE = MAX_FILE_MB * 1024 * 1024;
const EMAIL_RX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const state = {
  token: localStorage.getItem(TOKEN_KEY) || '',
  isSending: false,
  notifInterval: null,
  shownNotifs: new Set(),
  reminderQueue: [],
  currentReminderId: null,
  pendingFile: null,
  lastDays: [],
  lastReminders: [],
  lastPlan: {active:[],remaining:[],counts:{}},
  studentName: '',
  lastStudent: {},
};

const TWEAKS = /*EDITMODE-BEGIN*/{
  "accent": "indigo",
  "density": 1.1,
  "radius": 18,
  "theme": "dark"
}/*EDITMODE-END*/;

const ACCENTS = {
  indigo:  { a:'235 91% 64%', a2:'268 86% 68%' },
  blue:    { a:'215 90% 60%', a2:'195 90% 55%' },
  emerald: { a:'160 80% 42%', a2:'180 75% 45%' },
  rose:    { a:'350 85% 60%', a2:'330 80% 60%' },
  amber:   { a:'30 95% 55%',  a2:'15 90% 58%' },
  slate:   { a:'220 15% 45%', a2:'225 15% 55%' },
};

function applyTweaks(){
  const ac = ACCENTS[TWEAKS.accent] || ACCENTS.indigo;
  document.documentElement.style.setProperty('--accent', ac.a);
  document.documentElement.style.setProperty('--accent-2', ac.a2);
  document.documentElement.style.setProperty('--density', TWEAKS.density);
  document.documentElement.style.setProperty('--radius', TWEAKS.radius+'px');
  document.documentElement.dataset.theme = TWEAKS.theme;
  const sun = '<path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/><circle cx="12" cy="12" r="5"/>';
  const moon = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>';
  $('themeIcon').innerHTML = TWEAKS.theme === 'light' ? moon : sun;
}
function persistTweaks(patch){
  Object.assign(TWEAKS, patch);
  applyTweaks();
  try{ window.parent.postMessage({type:'__edit_mode_set_keys', edits: patch}, '*'); }catch{}
}
applyTweaks();

$('langBtn').onclick = () => {
  lang = lang === 'ar' ? 'en' : 'ar';
  localStorage.setItem(LANG_KEY, lang);
  applyLang();
};

function headers(extra={}){
  const out = {...extra};
  if(state.token) out['Authorization'] = `Bearer ${state.token}`;
  return out;
}
async function api(path, options={}){
  const timeoutMs = options._timeout ?? 30000;
  const { _timeout: _t, ...fetchOpts } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try{
    const res = await fetch(BASE + path, { ...fetchOpts, signal: controller.signal });
    const txt = await res.text();
    let data = null;
    try{ data = txt ? JSON.parse(txt) : null; } catch{ data = txt; }
    if(!res.ok) throw new Error((data && data.detail) || `Request failed (${res.status})`);
    return data;
  }catch(err){
    if(err.name === 'AbortError') throw new Error(lang === 'ar' ? 'انتهت مهلة الاتصال، حاول مجدداً' : 'Request timed out, please try again');
    throw err;
  }finally{
    clearTimeout(timer);
  }
}

let toastTimer;
function toast(msg, type=''){
  const t = $('toast');
  t.textContent = msg; t.className = 'toast show '+(type||'');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(()=>t.classList.remove('show'), 3000);
}

function showAuth(msg='', err=false){
  $('authWrap').style.display = 'grid';
  $('app').classList.remove('show');
  const m = $('authMsg');
  m.textContent = msg; m.className = 'auth-msg' + (err?' err':'');
}
function showApp(){
  $('authWrap').style.display = 'none';
  $('app').classList.add('show');
  if(!state.notifInterval){
    checkDueReminders();
    state.notifInterval = setInterval(checkDueReminders, 30000);
  }
}
document.querySelectorAll('[data-auth-tab]').forEach(b => {
  b.onclick = () => {
    document.querySelectorAll('[data-auth-tab]').forEach(x => x.classList.toggle('on', x===b));
    const tab = b.dataset.authTab;
    $('loginForm').style.display = tab==='login' ? 'block' : 'none';
    $('signupForm').style.display = tab==='signup' ? 'block' : 'none';
    $('authMsg').textContent = '';
  };
});

$('loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = $('loginBtn');
  btn.disabled = true;
  $('authMsg').className = 'auth-msg'; $('authMsg').textContent = t('auth.signing.in');
  try{
    const data = await api('/auth/login', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ email:$('liEmail').value.trim(), password:$('liPass').value }),
    });
    state.token = data.access_token;
    localStorage.setItem(TOKEN_KEY, state.token);
    showApp();
    applyLang();
    await Promise.all([loadDashboard(), loadHistory()]);
  }catch(err){
    $('authMsg').className = 'auth-msg err'; $('authMsg').textContent = err.message;
  }finally{ btn.disabled = false; }
});

$('signupForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = $('signupBtn');
  btn.disabled = true;
  $('authMsg').className = 'auth-msg'; $('authMsg').textContent = t('auth.signing.up');
  if(!EMAIL_RX.test($('suEmail').value.trim())){
    $('authMsg').className = 'auth-msg err';
    $('authMsg').textContent = lang === 'ar' ? 'البريد الإلكتروني غير صحيح' : 'Invalid email address';
    btn.disabled = false; return;
  }
  try{
    await api('/auth/signup', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        name:$('suName').value.trim(),
        email:$('suEmail').value.trim(),
        password:$('suPass').value,
        college:$('suCollege').value.trim() || null,
        major:$('suMajor').value || null,
        track:$('suTrack').value.trim() || null,
      }),
    });
    $('authMsg').className = 'auth-msg'; $('authMsg').textContent = t('auth.created');
    document.querySelector('[data-auth-tab="login"]').click();
    $('liEmail').value = $('suEmail').value;
  }catch(err){
    $('authMsg').className = 'auth-msg err'; $('authMsg').textContent = err.message;
  }finally{ btn.disabled = false; }
});

$('logoutBtn').onclick = () => {
  state.token = '';
  localStorage.removeItem(TOKEN_KEY);
  clearInterval(state.notifInterval); state.notifInterval = null;
  state.shownNotifs.clear(); state.reminderQueue = []; state.currentReminderId = null;
  $('reminderBg').classList.remove('show');
  showAuth(t('toast.logout'));
};

$('clearChatBtn').onclick = async () => {
  if(!confirm(t('confirm.clear'))) return;
  const btn = $('clearChatBtn');
  btn.disabled = true;
  try{
    await api('/chat/history', { method: 'DELETE', headers: headers() });
    await loadHistory();
    toast(t('toast.clear.ok'), 'ok');
  }catch(err){
    toast(err.message || t('toast.clear.err'), 'err');
  }finally{
    btn.disabled = false;
  }
};

function switchView(viewId){
  document.querySelectorAll('.view').forEach(v => v.classList.toggle('active', v.id === viewId));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.toggle('active', b.dataset.view === viewId));
  $('pageTitle').textContent = t('pt.' + viewId) || '';
  if(window.innerWidth <= 760){
    $('sidebar').classList.add('collapsed');
    $('sbBackdrop').classList.remove('show');
  }
  if(viewId === 'scheduleView') renderWeekGrid('weekGridFull', state.lastDays);
  if(viewId === 'remindersView') renderRemindersFull();
  if(viewId === 'chatView'){
    const cl = $('chatList');
    if(cl) requestAnimationFrame(() => { cl.scrollTop = cl.scrollHeight; });
  }
}
document.querySelectorAll('.nav-btn').forEach(b => b.onclick = () => switchView(b.dataset.view));
document.body.addEventListener('click', (e) => {
  const goBtn = e.target.closest('[data-go]');
  if(goBtn) switchView(goBtn.dataset.go);
});

$('menuBtn').onclick = () => {
  $('sidebar').classList.toggle('collapsed');
  $('sbBackdrop').classList.toggle('show');
};
$('sbBackdrop').onclick = () => {
  $('sidebar').classList.add('collapsed');
  $('sbBackdrop').classList.remove('show');
};
function applyMobileSidebarState(){
  if(window.innerWidth <= 760) $('sidebar').classList.add('collapsed');
  else $('sidebar').classList.remove('collapsed');
}
window.addEventListener('resize', applyMobileSidebarState);

$('themeBtn').onclick = () => {
  persistTweaks({ theme: TWEAKS.theme === 'light' ? 'dark' : 'light' });
};

function initialOf(name){
  const s = (name || '').trim();
  return s ? s[0] : (lang === 'ar' ? '؟' : '?');
}

function renderHeader(student){
  state.studentName = student.name || '';
  $('pName').textContent = student.name || t('default.student');
  const tags = [student.major, student.college].filter(Boolean).join(' • ');
  $('pMajor').textContent = tags || '—';
  $('avatar').textContent = initialOf(student.name);
  const hr = new Date().getHours();
  const greet = hr < 12 ? t('greet.morning') : t('greet.evening');
  const first = (student.name || t('default.student')).split(' ')[0];
  $('greetEl').textContent = `${greet}${t('greet.sep')}${first} 👋`;
}

function lecHTML(item){
  const code = item.course_code ? `<div class="code">${esc(item.course_code)}</div>` : '';
  const room = item.room_text ? esc(item.room_text) : '—';
  const roomBtn = item.image_url
    ? `<button class="room-link" data-img="${esc(item.image_url)}" data-title="${esc(item.room_text || item.course_name || '')}">${t('room.view.btn')}</button>`
    : '';
  return `
    <div class="lec">
      ${code}
      <div class="name">${esc(item.course_name || '')}</div>
      <div class="meta-row">
        <span>${esc(item.start_time || '--:--')} → ${esc(item.end_time || '--:--')}</span>
        <span>${room}</span>
      </div>
      ${roomBtn}
    </div>`;
}

const DAY_EN = {'الأحد':'Sunday','الاثنين':'Monday','الثلاثاء':'Tuesday','الأربعاء':'Wednesday','الخميس':'Thursday','الجمعة':'Friday','السبت':'Saturday'};
function renderWeekGrid(targetId, days){
  const el = $(targetId);
  if(!el) return;
  if(!Array.isArray(days) || !days.length){
    el.innerHTML = `<div class="empty" style="grid-column:1/-1">${t('schedule.empty')}</div>`;
    return;
  }
  const dayName = d => lang === 'ar' ? (d.day_name_ar || '') : (d.day_name_en || DAY_EN[d.day_name_ar] || d.day_name_ar || '');
  el.innerHTML = days.map(d => `
    <div class="day">
      <div class="day-head">
        <strong>${esc(dayName(d))}</strong>
        <span class="day-pill">${(d.items||[]).length} ${t('day.classes')}</span>
      </div>
      ${(d.items||[]).length ? d.items.map(lecHTML).join('') : `<div class="empty">${t('day.no.classes')}</div>`}
    </div>`).join('');
}

function rowHTML(r){
  const status = r.is_done ? 'done' : 'active';
  const label = r.is_done ? t('status.done') : t('status.active');
  return `
    <div class="row">
      <div class="title">
        <span>${esc(r.title || '')}</span>
        <div style="display:flex;align-items:center;gap:6px;flex-shrink:0">
          <span class="status-pill ${status}">${label}</span>
          <button class="rem-del-btn" data-del-rid="${r.reminder_id ?? r.id ?? ''}" title="${t('rem.del.title')}">🗑</button>
        </div>
      </div>
      <div class="meta-line">
        <span>${esc(r.remind_at_text || '')}</span>
        <span>${esc(r.notes || '')}</span>
      </div>
    </div>`;
}

function renderDashboard(data){
  state.lastDays = data.week_schedule?.days || [];
  state.lastReminders = data.recent_reminders || [];
  state.lastPlan = { active: data.academic_plan_active || [], remaining: data.academic_plan_remaining || [], counts: data.counts || {} };
  state.lastStudent = data.student || {};

  renderHeader(state.lastStudent);
  $('mWeek').textContent = data.counts.week_classes ?? 0;
  $('mAll').textContent = data.counts.all_classes ?? 0;
  $('mRem').textContent = data.counts.active_reminders ?? 0;
  $('mPlan').textContent = (data.counts.remaining_courses ?? 0) + (data.counts.active_courses ?? 0);

  renderWeekGrid('weekGrid', state.lastDays);
  const remEl = $('remListShort');
  const rems = state.lastReminders.slice(0,4);
  remEl.innerHTML = rems.length ? rems.map(rowHTML).join('') : `<div class="empty">${t('rem.empty.short')}</div>`;
  renderPlan();
}

function renderPlan(){
  const { active, remaining, counts } = state.lastPlan || {active:[],remaining:[],counts:{}};
  const total = counts.plan_items || 0;
  const ps = $('planSummary');
  if(total){
    ps.style.display = 'flex';
    ps.innerHTML = `
      <span>${t('plan.completed')}<strong>${counts.completed_courses ?? 0}</strong></span>
      <span>${t('plan.in.progress')}<strong>${counts.active_courses ?? 0}</strong></span>
      <span>${t('plan.remaining')}<strong>${counts.remaining_courses ?? 0}</strong></span>
      <span>${t('plan.total')}<strong>${total}</strong></span>`;
  } else { ps.style.display = 'none'; }

  $('planActiveLabel').hidden = !active.length;
  $('planActiveList').innerHTML = active.map(it => `
    <div class="row">
      <div class="title">
        <span>${esc(it.course_name || '')}</span>
        <span class="status-pill in-progress">${t('plan.status.active')}</span>
      </div>
      <div class="meta-line"><span>${esc(it.course_code || '')}</span><span>${esc(it.semester || '')}</span></div>
    </div>`).join('');

  $('planRemainingLabel').hidden = !remaining.length;
  $('planRemainingList').innerHTML = remaining.map(it => `
    <div class="row">
      <div class="title">
        <span>${esc(it.course_name || '')}</span>
        <span class="status-pill remaining">${t('plan.status.remaining')}</span>
      </div>
      <div class="meta-line"><span>${esc(it.course_code || '')}</span><span>${esc(it.semester || '')}</span></div>
    </div>`).join('');

  if(!active.length && !remaining.length){
    $('planRemainingLabel').hidden = true;
    $('planRemainingList').innerHTML = `<div class="empty">${t('plan.empty')}</div>`;
  }
}

function renderRemindersFull(){
  const list = state.lastReminders || [];
  $('remListFull').innerHTML = list.length ? list.map(rowHTML).join('') : `<div class="empty">${t('rem.empty.full')}</div>`;
}

async function loadDashboard(){
  try{
    const data = await api('/dashboard/summary', { headers: headers() });
    renderDashboard(data);
  }catch(e){
    if(String(e.message).includes('401')) throw e;
  }
}

function metaHTML(meta){
  if(!meta || typeof meta !== 'object') return '';
  let html = '<div class="meta-group">';
  let added = false;
  if(Array.isArray(meta.items) && meta.items.length){
    added = true;
    html += meta.items.map(it => `
      <div class="meta-card">
        ${it.course_code ? `<div style="font-size:11px;color:var(--muted)">${esc(it.course_code)}</div>` : ''}
        <h5>${esc(it.course_name || '')}</h5>
        <div class="row-line">
          <span>${esc(it.start_time || '--:--')} → ${esc(it.end_time || '--:--')}</span>
          <span>${esc(it.room_text || '')}${it.image_url ? ` <button class="room-link" data-img="${esc(it.image_url)}" data-title="${esc(it.room_text||it.course_name||'')}">عرض</button>` : ''}</span>
        </div>
      </div>`).join('');
  }
  if(Array.isArray(meta.reminders) && meta.reminders.length){
    added = true;
    html += meta.reminders.map(it => `
      <div class="meta-card">
        <h5>${esc(it.title || '')}</h5>
        <div class="row-line"><span>${esc(it.remind_at_text || '')}</span><span>${it.is_done ? t('status.done') : t('status.active')}</span></div>
      </div>`).join('');
  }
  if(Array.isArray(meta.academic_plan) && meta.academic_plan.length){
    added = true;
    html += meta.academic_plan.map(it => `
      <div class="meta-card">
        <h5>${esc(it.course_name || '')}</h5>
        <div class="row-line"><span>${esc(it.course_code || '')}</span><span>${esc(it.status || '')}</span></div>
      </div>`).join('');
  }
  if(typeof meta.added === 'number'){
    added = true;
    html += `
      <div class="meta-card">
        <h5>${t('import.title')}</h5>
        <div class="row-line"><span>${t('import.added')}</span><span>${esc(meta.added)}</span></div>
        ${Array.isArray(meta.skipped) && meta.skipped.length ? `<div class="row-line"><span>${t('import.skipped')}</span><span>${esc(meta.skipped.length)}</span></div>` : ''}
      </div>`;
  }
  html += '</div>';
  return added ? html : '';
}

function renderMd(text){
  let s = (text || '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  s = s.replace(/\*\*([^*\n]+?)\*\*/g,'<strong>$1</strong>');
  s = s.replace(/\*([^*\n]+?)\*/g,'<em>$1</em>');
  return s;
}
function clearWelcome(){ const w = $('chatWelcome'); if(w) w.remove(); }
function addMessage(role, text, meta=null, isTyping=false){
  clearWelcome();
  const el = document.createElement('div');
  el.className = `msg ${role}`;
  const av = role === 'user' ? (initialOf(state.studentName) || (lang==='ar'?'أ':'S')) : (lang==='ar'?'ج':'A');
  const bubbleContent = isTyping
    ? '<div class="typing"><span></span><span></span><span></span></div>'
    : (role === 'assistant' ? renderMd(text || '') : esc(text || ''));
  el.innerHTML = `
    <div class="msg-avatar">${av}</div>
    <div class="msg-content" style="min-width:0;flex:1">
      <div class="bubble">${bubbleContent}</div>
      ${metaHTML(meta)}
    </div>`;
  $('chatList').appendChild(el);
  $('chatList').scrollTop = $('chatList').scrollHeight;
  return el;
}

async function loadHistory(){
  try{
    const hist = await api('/chat/history', { headers: headers() });
    $('chatList').innerHTML = '';
    if(!Array.isArray(hist) || !hist.length){
      $('chatList').innerHTML = `
        <div class="welcome" id="chatWelcome">
          <div class="big">${t('chat.welcome.big')}</div>
          <p>${t('chat.welcome.p')}</p>
          <div class="suggestion-grid">
            <button class="suggestion" data-prompt="وش عندي اليوم؟"><span>${t('chat.s1')}</span><span class="hint">${t('chat.s1.hint')}</span></button>
            <button class="suggestion" data-prompt="أضف واجب الذكاء الاصطناعي يوم الأربعاء 11 مساءً"><span>${t('chat.s2')}</span><span class="hint">${t('chat.s2.hint')}</span></button>
            <button class="suggestion" data-prompt="اقترح علي مواد مناسبة للفصل الجاي"><span>${t('chat.s3')}</span><span class="hint">${t('chat.s3.hint')}</span></button>
            <button class="suggestion" data-prompt="ما هي قواعد الانذار الأكاديمي؟"><span>${t('chat.s4')}</span><span class="hint">${t('chat.s4.hint')}</span></button>
          </div>
        </div>`;
      return;
    }
    hist.forEach(m => {
      let meta = null;
      if(m.meta_json){ try{ meta = JSON.parse(m.meta_json); }catch{} }
      addMessage(m.role === 'user' ? 'user' : 'assistant', m.content, meta);
    });
  }catch(e){
    if(String(e.message).includes('401')) throw e;
  }
}

function updateSendBtn(){
  $('sendBtn').disabled = state.isSending || (!$('chatInput').value.trim() && !state.pendingFile);
}
function setSending(s){ state.isSending = s; updateSendBtn(); }
function setAttachment(file){
  if(file && file.size > MAX_FILE_SIZE){
    toast(lang === 'ar' ? `الملف أكبر من ${MAX_FILE_MB} ميجابايت` : `File exceeds ${MAX_FILE_MB} MB`, 'err');
    $('chatImgInput').value = '';
    return;
  }
  state.pendingFile = file || null;
  const chip = $('attachChip');
  if(file){ $('attachName').textContent = file.name; chip.classList.add('show'); }
  else { chip.classList.remove('show'); $('chatImgInput').value = ''; }
  updateSendBtn();
}

async function sendMessage(prefilled){
  if(state.isSending) return;
  const file = state.pendingFile;
  const raw = prefilled ?? $('chatInput').value;
  const msg = (raw || '').trim();
  if(!msg && !file) return;

  switchView('chatView');
  $('chatInput').value = ''; autoresize($('chatInput'));
  setSending(true);

  if(file){
    addMessage('user', msg ? `${msg}\n[image: ${file.name}]` : `${t('uploaded.image')}${file.name}`);
  } else {
    addMessage('user', msg);
  }
  const typingEl = addMessage('assistant', '', null, true);

  try{
    let data;
    if(file){
      const form = new FormData();
      form.append('message', msg);
      form.append('file', file);
      data = await api('/chat/with-image', { _timeout: 120000, method:'POST', headers: headers(), body: form });
    } else {
      data = await api('/chat', {
        _timeout: 90000,
        method:'POST',
        headers: headers({'Content-Type':'application/json'}),
        body: JSON.stringify({ message: msg }),
      });
    }
    typingEl.querySelector('.bubble').innerHTML = renderMd(data.text || '');
    const wrap = document.createElement('div'); wrap.innerHTML = metaHTML(data.meta || null);
    if(wrap.firstChild) typingEl.querySelector('.msg-content').appendChild(wrap.firstChild);
    setAttachment(null);
    loadDashboard().catch(err => console.warn('[chat] dashboard reload', err));
    checkDueReminders().catch(err => console.warn('[chat] reminder check', err));
  } catch(err){
    typingEl.querySelector('.bubble').innerHTML = `<span style="color:#fca5a5">⚠️ ${esc(err.message)}</span>`;
  } finally {
    setSending(false);
    $('chatList').scrollTop = $('chatList').scrollHeight;
  }
}

function autoresize(t){
  t.style.height = 'auto';
  t.style.height = Math.min(t.scrollHeight, 160) + 'px';
}
$('chatInput').addEventListener('input', (e) => { autoresize(e.target); updateSendBtn(); });
$('chatInput').addEventListener('keydown', (e) => {
  if(e.key === 'Enter' && !e.shiftKey){ e.preventDefault(); sendMessage(); }
});
$('sendBtn').onclick = () => sendMessage();
$('attachBtn').onclick = () => $('chatImgInput').click();
$('chatImgInput').addEventListener('change', (e) => setAttachment(e.target.files?.[0] || null));
$('attachRemove').onclick = () => setAttachment(null);

document.body.addEventListener('click', async (e) => {
  const p = e.target.closest('[data-prompt]');
  if(p){ const q = p.dataset.prompt; if(q) sendMessage(q); }
  const ri = e.target.closest('[data-img]');
  if(ri){ _lastRoomTrigger = ri; openImg(ri.dataset.img, ri.dataset.title); }
  const delBtn = e.target.closest('[data-del-rid]');
  if(delBtn){
    const rid = delBtn.dataset.delRid;
    if(!rid) return;
    delBtn.disabled = true;
    try{
      await api(`/dashboard/reminders/${rid}`, { method:'DELETE', headers: headers() });
      delBtn.closest('.row')?.remove();
      loadDashboard().catch(()=>{});
    }catch(err){
      toast(err.message || t('toast.del.err'), 'err');
      delBtn.disabled = false;
    }
  }
});

async function uploadFile(endpoint, file, label){
  switchView('chatView');
  addMessage('user', `${label}: ${file.name}`);
  const typingEl = addMessage('assistant', '', null, true);
  try{
    const form = new FormData(); form.append('file', file);
    const data = await api(endpoint, { _timeout: 120000, method:'POST', headers: headers(), body: form });
    typingEl.querySelector('.bubble').innerHTML = renderMd(data.text || '');
    const wrap = document.createElement('div'); wrap.innerHTML = metaHTML(data.meta || null);
    if(wrap.firstChild) typingEl.querySelector('.msg-content').appendChild(wrap.firstChild);
    loadDashboard().catch(err => console.warn('[upload] dashboard reload', err));
    loadHistory().catch(err => console.warn('[upload] history reload', err));
    toast(t('toast.import.ok'));
  } catch(err){
    typingEl.querySelector('.bubble').innerHTML = `<span style="color:#fca5a5">⚠️ ${esc(err.message)}</span>`;
    toast(t('toast.import.err') + err.message, 'err');
  }
}
function pickFile(input, endpoint, label){
  input.value = '';
  input.click();
  input.onchange = () => {
    const f = input.files?.[0]; if(!f) return;
    if(f.size > MAX_FILE_SIZE){
      toast(lang === 'ar' ? `الملف أكبر من ${MAX_FILE_MB} ميجابايت` : `File exceeds ${MAX_FILE_MB} MB`, 'err');
      input.value = ''; return;
    }
    uploadFile(endpoint, f, label);
    input.value = '';
  };
}
$('uploadScheduleBtn').onclick = () => pickFile($('scheduleImgInput'), '/chat/upload-schedule-image', 'رفع صورة جدول');
$('uploadScheduleBtn2').onclick = () => pickFile($('scheduleImgInput'), '/chat/upload-schedule-image', 'رفع صورة جدول');
$('uploadPlanBtn').onclick = () => pickFile($('planImgInput'), '/chat/upload-plan-image', 'رفع صورة خطة أكاديمية');

let _lastRoomTrigger = null;
function openImg(src, title){
  $('imgModalImg').src = src;
  $('imgModalTitle').textContent = title || t('modal.room.title');
  $('imgModal').classList.add('show');
  requestAnimationFrame(() => $('imgModalClose').focus());
}
$('imgModalClose').onclick = () => {
  $('imgModal').classList.remove('show');
  $('imgModalImg').src = '';
  if(_lastRoomTrigger){ _lastRoomTrigger.focus(); _lastRoomTrigger = null; }
};
$('imgModal').addEventListener('click', (e) => { if(e.target === $('imgModal')) $('imgModalClose').click(); });

function fmtAt(iso, fallback){
  if(!iso) return fallback || '';
  try{
    const d = new Date(iso);
    const now = new Date();
    const isToday = d.toDateString() === now.toDateString();
    const tomorrow = new Date(now); tomorrow.setDate(now.getDate()+1);
    const isTom = d.toDateString() === tomorrow.toDateString();
    const loc = t('locale');
    const tm = d.toLocaleTimeString(loc, {hour:'2-digit',minute:'2-digit'});
    if(isToday) return `${t('time.today')}${tm}`;
    if(isTom) return `${t('time.tomorrow')}${tm}`;
    return d.toLocaleDateString(loc,{weekday:'short',month:'short',day:'numeric'}) + ' ' + tm;
  }catch{ return fallback || iso; }
}
function playReminderSound(){
    try{
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    [[880,0,0.15],[660,0.18,0.12],[880,0.32,0.18]].forEach(([freq,start,dur])=>{
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain); gain.connect(ctx.destination);
      osc.type = 'sine'; osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.25, ctx.currentTime + start);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + start + dur);
      osc.start(ctx.currentTime + start);
      osc.stop(ctx.currentTime + start + dur + 0.05);
    });
  }catch{}
}
function showNextReminder(){
  if(!state.reminderQueue.length){
    $('reminderBg').classList.remove('show'); state.currentReminderId = null; return;
  }
  const r = state.reminderQueue.shift();
  state.currentReminderId = r.reminder_id;
  $('rTitle').textContent = r.title || '';
  $('rTime').textContent = fmtAt(r.remind_at, r.remind_at_text) + (r.notes ? '\n'+r.notes : '');
  $('rCounter').textContent = state.reminderQueue.length ? t('reminder.more').replace('{n}', state.reminderQueue.length) : '';
  $('reminderBg').classList.add('show');
  requestAnimationFrame(() => $('rDoneBtn').focus());
  playReminderSound();
}
$('rDoneBtn').onclick = async () => {
  const id = state.currentReminderId;
  state.currentReminderId = null;
  showNextReminder();
  if(id != null){
    try{
      await api(`/dashboard/reminders/${id}/done`, { method:'POST', headers: headers() });
      loadDashboard().catch(err => console.warn('[reminders]', err));
    }catch(err){ console.warn('[reminder done]', err); }
  }
};
$('rOkBtn').onclick = () => { state.currentReminderId = null; showNextReminder(); };
async function checkDueReminders(){
  if(!state.token) return;
  try{
    const data = await api('/dashboard/reminders/due', { headers: headers() });
    (data.reminders || []).forEach(r => {
      if(state.shownNotifs.has(r.reminder_id)) return;
      state.shownNotifs.add(r.reminder_id);
      const wasIdle = !state.reminderQueue.length && state.currentReminderId === null;
      state.reminderQueue.push(r);
      if(wasIdle) showNextReminder();
    });
  }catch(err){ console.warn('[reminders check]', err); }
}

async function pingHealth(){
  const setHealth = (state, bad) => {
    $('healthDot').classList.toggle('bad', bad);
    const hl = $('healthLabel');
    hl.dataset.healthState = state;
    hl.textContent = t('health.' + state);
  };
  try{
    const h = await api('/health');
    setHealth(h?.status === 'ok' ? 'ok' : 'offline', h?.status !== 'ok');
  }catch{
    setHealth('unavailable', true);
  }
}

const accentEntries = Object.keys(ACCENTS);
function renderAccents(){
  $('accentSwatches').innerHTML = accentEntries.map(name => {
    const c = ACCENTS[name];
    return `<button class="swatch ${name===TWEAKS.accent?'on':''}" data-accent="${name}"
      style="background:linear-gradient(135deg,hsl(${c.a}),hsl(${c.a2}))"></button>`;
  }).join('');
  $('accentSwatches').querySelectorAll('.swatch').forEach(b => b.onclick = () => {
    persistTweaks({ accent: b.dataset.accent });
    renderAccents();
  });
}
renderAccents();
$('densitySeg').querySelectorAll('button').forEach(b => {
  b.classList.toggle('on', parseFloat(b.dataset.val) === TWEAKS.density);
  b.onclick = () => {
    persistTweaks({ density: parseFloat(b.dataset.val) });
    $('densitySeg').querySelectorAll('button').forEach(x => x.classList.toggle('on', x===b));
  };
});
$('radiusSeg').querySelectorAll('button').forEach(b => {
  b.classList.toggle('on', parseInt(b.dataset.val) === TWEAKS.radius);
  b.onclick = () => {
    persistTweaks({ radius: parseInt(b.dataset.val) });
    $('radiusSeg').querySelectorAll('button').forEach(x => x.classList.toggle('on', x===b));
  };
});

window.addEventListener('message', (e) => {
  const t = e.data?.type;
  if(t === '__activate_edit_mode'){
    $('tweaksPanel').classList.add('show');
    $('tweaksBtn').style.display = 'grid';
  } else if(t === '__deactivate_edit_mode'){
    $('tweaksPanel').classList.remove('show');
  }
});
$('tweaksBtn').onclick = () => $('tweaksPanel').classList.toggle('show');
$('tweaksClose').onclick = () => {
  $('tweaksPanel').classList.remove('show');
  try{ window.parent.postMessage({type:'__edit_mode_dismissed'}, '*'); }catch{}
};
try{ window.parent.postMessage({type:'__edit_mode_available'}, '*'); }catch{}

async function init(){
  applyMobileSidebarState();
  applyLang();
  pingHealth();
  setInterval(pingHealth, 60000);
  updateSendBtn();
  if(state.token){
    try{
      await Promise.all([loadHistory(), loadDashboard()]);
      showApp();
      applyLang();
    }catch{
      state.token=''; localStorage.removeItem(TOKEN_KEY);
      showAuth(t('auth.session.expired'), true);
    }
  } else {
    showAuth('');
  }
}
init();
