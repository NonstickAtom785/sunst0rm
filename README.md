# **sunst0rm**
iOS Tether Downgrader for checkm8 devices

An automated solution to [my previous guide](https://github.com/mineek/iostethereddowngrade).

## Join the [Discord](https://discord.gg/TqVH6NBwS3) server for help

## **Requirements**:
- [libirecovery](https://github.com/libimobiledevice/libirecovery)
- [futurerestore (fork)](https://github.com/futurerestore/futurerestore)
   - futurerestore must be the nightly build. A compiled binary can be found [here](https://nightly.link/futurerestore/futurerestore/workflows/ci/test)
- [iBoot64patcher (fork)](https://github.com/Cryptiiiic/iBoot64Patcher)
- [Kernel64patcher (fork)](https://github.com/iSuns9/Kernel64Patcher)
- [img4tool](https://github.com/tihmstar/img4tool)
- [img4](https://github.com/xerub/img4lib)
- [ldid](https://github.com/ProcursusTeam/ldid)
- [restored_external64_patcher (fork)](https://github.com/iSuns9/restored_external64patcher)
- [asr64_patcher](https://github.com/exploit3dguy/asr64_patcher)
- [Python3](https://www.python.org/downloads)
   - Make sure you updated Python and are not using the bundled one in macOS
- Python dependencies
   - `pip3 install -r requirements.txt`

**Make sure to use the forks listed above.**

## How to use?
| **Flag[Short]** | **Description**                          |
|-----------------|------------------------------------------|
| ispw[-i] `IPSW`              | Path to IPSW                          |
| blob[-t] `SHSH2`             | Path to SHSH2                         |
| restore[-r] `true`           | Restore mode                          |
| boot[-b] `true`              | Boot mode                             |
| boardconfig[-d] `BOARDCONFIG`| BoardConfig to use  (E.g: `d221ap`)   |
| kpp[-kpp] `true`             | Use KPP (A9 or lower)                 |
| identifier[-id] `IDENTIFIER` | Identifier to use  (E.g: `iPhone10,6`)|
| legacy `true`                | Use Legacy Mode (iOS 11 or lower)     |

### Restoring
```py
python3 sunstorm.py -i 'IPSW' -t 'SHSH2' -r true -d 'BOARDCONFIG'
```
- Use `--kpp true` if you have KPP, otherwise don't add
### Booting
```py
python3 sunstorm.py -i 'IPSW' -t 'SHSH2' -b true -d 'BOARDCONFIG' -id 'IDENTIFIER'
```
- Use `--kpp true` if you have KPP, otherwise don't add
```
./boot.sh
```

## Credits:
[M1n1Exploit](https://github.com/Mini-Exploit) - Some code from ra1nstorm
