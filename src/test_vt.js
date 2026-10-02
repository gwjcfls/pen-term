import term from 'term';

function show(tag, v) { console.log(tag + ' = ' + JSON.stringify(v)); }

console.log('=== 测试1：真实 top 输出（110x11 网格）===');
var r = term.spawn('top -b -n1 2>&1 | head -20', { cols: 110, rows: 11 });
show('spawn', r);
show('vtStart', term.vtStart(r.sid, 110, 11, '/userdisk/term'));
term.execSync('sleep 2', 4000);
show('vtFeed', term.vtFeed(r.sid));
var img = term.vtRender(r.sid);
show('vtRender', img);
console.log('--- 屏幕文本 ---');
console.log(term.vtText(r.sid));
console.log('--- 结束 ---');

console.log('=== 测试2：颜色 + 制表符 + 反白 ===');
var cmd2 = "printf '\\033[1;32mGREEN-BOLD\\033[0m plain \\033[41mRED-BG\\033[0m \\033[4mUNDERLINE\\033[0m\\n'; " +
  "printf '+--------+--------+\\n| cell   | value  |\\n+--------+--------+\\n'; " +
  "printf 'blocks: '; for i in 1 2 3 4 5 6; do printf '\\033[4%dm[]\\033[0m' $i; done; echo";
var r2 = term.spawn(cmd2, { cols: 110, rows: 11 });
show('spawn2', r2);
show('vtStart2', term.vtStart(r2.sid, 110, 11, '/userdisk/term'));
term.execSync('sleep 2', 4000);
show('vtFeed2', term.vtFeed(r2.sid));
var img2 = term.vtRender(r2.sid);
show('vtRender2', img2);
console.log(term.vtText(r2.sid));
console.log('=== done ===');
