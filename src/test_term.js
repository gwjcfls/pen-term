import term from 'term';

console.log('=== info ===');
console.log(JSON.stringify(term.info()));

console.log('=== 本地 PTY 会话 ===');
var r = term.spawnShell('/tmp');
console.log('spawnShell -> ' + JSON.stringify(r));
if (r && r.sid) {
  term.write(r.sid, 'echo MARK_PTY_OK; id; pwd; ls / | head -3\n');
  term.execSync('sleep 1', 3000);
  console.log('--- PTY 输出 ---');
  console.log(term.read(r.sid, 8000));
  console.log('alive=' + term.alive(r.sid));
  term.kill(r.sid);
}

console.log('=== execSync ===');
var e = term.execSync('uname -m; whoami; ls /usr/bin | wc -l', 5000);
console.log('code=' + e.code + ' out=' + JSON.stringify(e.out));

console.log('=== 生成测试密钥并起 sshd ===');
term.execSync("mkdir -p /userdisk/ssh; [ -f /userdisk/ssh/id_test ] || ssh-keygen -q -t ed25519 -N '' -f /userdisk/ssh/id_test", 10000);
var pub = term.execSync('cat /userdisk/ssh/id_test.pub', 3000);
console.log('pub=' + String(pub.out || '').trim().slice(0, 70));
var sd = term.sshdStart(2222, pub.out);
console.log('sshdStart=' + JSON.stringify(sd));
term.execSync('sleep 2', 4000);
console.log('sshdStatus=' + JSON.stringify(term.sshdStatus()));

console.log('=== SSH 客户端 -> 本机 sshd ===');
var s2 = term.spawnSsh('127.0.0.1', 'root', 2222, null, '-i/userdisk/ssh/id_test');
console.log('spawnSsh=' + JSON.stringify(s2));
if (s2 && s2.sid) {
  term.execSync('sleep 2', 4000);
  term.write(s2.sid, 'echo SSH_CLIENT_OK; id; hostname\n');
  term.execSync('sleep 2', 4000);
  console.log('--- SSH 输出 ---');
  console.log(term.read(s2.sid, 8000));
  console.log('alive=' + term.alive(s2.sid));
  term.kill(s2.sid);
}
console.log('=== done ===');
