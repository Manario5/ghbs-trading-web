require('child_process').exec('ss -tlnp', (err, stdout) => { console.log(stdout); });
