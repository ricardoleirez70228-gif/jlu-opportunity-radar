#!/usr/bin/env python3
"""Collect public university announcements; does not authenticate to OA."""
import json,os,re,smtplib
from pathlib import Path
from datetime import datetime,date,timedelta
from email.message import EmailMessage
from urllib.parse import urljoin,urlsplit
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup
BASE=Path(__file__).parent
DB=BASE/'data/notices.json'
NOW=datetime.now(ZoneInfo('Asia/Shanghai'))
HEADER={'User-Agent':'Mozilla/5.0 (JLU public notice personal academic monitor)'}
KEYS={
'奖助学金':['奖学金','助学金','励学金','学术业绩','奖助'],
'竞赛机会':['竞赛','比赛','挑战赛','案例大赛','创新创业','商业分析'],
'科研项目':['科研项目','课题','立项','项目申报','征稿','科研基金'],
'学术活动':['学术报告','学术会议','讲座','学术论坛','学术沙龙','研讨会'],
'评奖评优':['评优','优秀研究生','先进个人','优秀学生干部','推优'],
'培养发展':['培养','访学','国际交流','实践','就业招聘','研究生会']}
FULL=re.compile(r'(20\d{2})[年./-](\d{1,2})[月./-](\d{1,2})日?')
SHORT=re.compile(r'(\d{1,2})月(\d{1,2})日')
DEADLINE=re.compile(r'(?:截止|截至|申报|申请|提交|报送|报名).{0,35}?(20\d{2}[年./-]\d{1,2}[月./-]\d{1,2}日?|\d{1,2}月\d{1,2}日)',re.S)
def valid(url):
 p=urlsplit(url)
 h=(p.hostname or '').lower()
 return p.scheme=='https' and (h=='jlu.edu.cn' or h.endswith('.jlu.edu.cn')) and h!='oa.jlu.edu.cn'
def dateval(text,year=None):
 m=FULL.search(text)
 if m: bits=list(map(int,m.groups()))
 else:
  m=SHORT.search(text)
  if not m:return ''
  bits=[year or NOW.year,*map(int,m.groups())]
 try:return date(*bits).isoformat()
 except ValueError:return ''
def classify(title):
 scores={cat:sum(w in title for w in words) for cat,words in KEYS.items()}
 best=max(scores,key=scores.get)
 return best if scores[best] else None
def eligibility(text):
 if any(k in text for k in ('仅限本科生','本科生专属','本科生“','本科生\"','本科生学科竞赛','仅限博士','博士生专属','MBA专属','MPAcc专属','仅限专业学位')):
  return '明显不适用'
 return '适用资格需核实'
def fetch(url):
 if not valid(url):raise ValueError('Nonpublic or non-JLU address rejected')
 r=requests.get(url,headers=HEADER,timeout=20)
 r.raise_for_status()
 if not valid(r.url):raise ValueError('Unexpected redirect')
 if r.encoding and r.encoding.lower() in ('iso-8859-1','ascii'):r.encoding=r.apparent_encoding
 return BeautifulSoup(r.text,'html.parser')
def listing(source):
 soup=fetch(source['url']);out={}
 for a in soup.select('a[href]'):
  title=' '.join(a.stripped_strings)
  title=re.sub(r'\s+',' ',title).strip()
  if len(title)<10 or len(title)>120:continue
  cat=classify(title)
  if not cat:continue
  link=urljoin(source['url'],a.get('href',''))
  if not valid(link) or link==source['url']:continue
  row=' '.join((a.parent or a).stripped_strings)[:300]
  published=dateval(row)
  # Listing rows sometimes carry only a day and month (e.g. '21 2026-10').
  if not published:
   lm=re.search(r'(?<!\\d)([0-3]?\\d)\\s+(20\\d{2})[-./](\\d{1,2})(?!\\d)',row)
   if lm:
    try:published=date(int(lm.group(2)),int(lm.group(3)),int(lm.group(1))).isoformat()
    except ValueError:pass
  # Avoid claiming dates not present on the listing; article page may supply date.
  out[link]={'title':title,'url':link,'source':source['name'],
   'priority':source.get('priority',1),'category':cat,'published':published,
   'deadline':'','eligibility':eligibility(title),'summary':'请打开原文核实附件与申请条件。',
   'first_seen':NOW.date().isoformat()}
 return list(out.values())
def enrich(n):
 try:
  soup=fetch(n['url'])
  for t in soup(['script','style','header','footer','nav']):t.decompose()
  body=soup.select_one('.v_news_content, .wp_articlecontent, #vsb_content, .article-content, .news-content') or soup
  text=re.sub(r'\s+',' ',body.get_text(' ',strip=True))[:18000]
  if text:n['summary']=text[:180]+('…' if len(text)>180 else '')
  if not n['published']:
   for css in ('.date','.time','.publishdate','.article-info','.info'):
    el=soup.select_one(css)
    if el:
     n['published']=dateval(el.get_text(' ',strip=True))
     if n['published']:break
  m=DEADLINE.search(text)
  if m:
   n['deadline']=dateval(m.group(1),int(n['published'][:4]) if n['published'] else NOW.year)
   # Ignore suspicious historic year mismatches until manually verified.
   if n['deadline'] and n['published'] and n['deadline'][:4]!=n['published'][:4]:n['deadline']=''
   n['deadline_evidence']=text[max(0,m.start()-15):m.end()+12][:110]
 except Exception as e:print('DETAIL ERROR',n['url'],repr(e)[:140])
 return n
def email_new(entries):
 if not entries or not all(os.getenv(k) for k in ('SMTP_HOST','SMTP_USER','SMTP_PASSWORD','NOTICE_TO')):return
 mail=EmailMessage();mail['Subject']=f'吉林大学企业管理学硕机会雷达：新增{len(entries)}条'
 mail['From']=os.getenv('NOTICE_FROM') or os.environ['SMTP_USER'];mail['To']=os.environ['NOTICE_TO']
 lines=['今日公开网站新发现的通知（请以原文为准）：','']
 for n in entries[:30]:
  lines += [f"【{n['category']}】{n['title']}",f"来源：{n['source']}；截止日期：{n['deadline'] or '待核实'}",n['url'],'']
 mail.set_content('\n'.join(lines))
 with smtplib.SMTP_SSL(os.environ['SMTP_HOST'],int(os.getenv('SMTP_PORT','465')),timeout=20) as s:
  s.login(os.environ['SMTP_USER'],os.environ['SMTP_PASSWORD']);s.send_message(mail)
def main():
 old=json.loads(DB.read_text(encoding='utf8')) if DB.exists() else {'notices':[]}
 saved={x['url']:x for x in old.get('notices',[])}
 fresh=[];sources=[];errors=[]
 for src in json.loads((BASE/'sources.json').read_text(encoding='utf8')):
  try:
   found=listing(src);new=0
   for n in found:
    if n['url'] in saved:continue
    n=enrich(n);saved[n['url']]=n;fresh.append(n);new+=1
   sources.append({'name':src['name'],'ok':True,'count':len(found),'new':new})
  except Exception as e:
   sources.append({'name':src['name'],'ok':False,'count':0,'new':0})
   errors.append({'source':src['name'],'error':str(e)[:180]});print('SOURCE ERROR',src['name'],repr(e))
 cutoff=(NOW.date()-timedelta(days=365)).isoformat()
 notices=[x for x in saved.values() if not x.get('published') or x['published']>=cutoff]
 notices.sort(key=lambda x:(x.get('published',''),x.get('first_seen','')),reverse=True)
 for n in notices:
  n['eligibility']=eligibility(n.get('title',''))
  # For events, the event date is not a publication date; correct obvious confusion.
  if n.get('published') and any(w in n.get('title','') for w in ('报告时间','讲座时间')):
   n['published']=''
  # Evidence from a different year is not a reliable current deadline.
  ev=n.get('deadline_evidence','')
  if n.get('deadline') and re.search(r'20\\s*2\\s*5',ev) and n['deadline'].startswith('2026'):
   n['deadline']=''
 out={'updated':NOW.strftime('%Y-%m-%d %H:%M 北京时间'),'updated_iso':NOW.isoformat(),
  'notices':notices[:1200],'new_count':len(fresh),'sources':sources,'errors':errors,'mode':'public-only'}
 DB.parent.mkdir(exist_ok=True)
 DB.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
 print('TOTAL',len(notices),'NEW',len(fresh),'SOURCE ERRORS',len(errors))
 if not any(x['ok'] for x in sources):raise SystemExit('All sources unavailable; previous notices preserved')
 email_new([n for n in fresh if n['eligibility']!='明显不适用'])
if __name__=='__main__':main()
