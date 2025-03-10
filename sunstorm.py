import argparse
import os
import sys
import zipfile
from manifest import Manifest
import api
import subprocess

def dependencies():
    import os
    import sys
    import subprocess
    if not os.path.exists('/usr/local/bin/futurerestore'):
        print('[!] futurerestore not found, please install it')
        sys.exit(1)
    if not os.path.exists('/usr/local/bin/img4tool'):
        print('[!] img4tool not found, please install it')
        sys.exit(1)
    if not os.path.exists('/usr/local/bin/img4'):
        print('[!] img4 not found, please install it')
        sys.exit(1)
    if not os.path.exists('/usr/local/bin/Kernel64Patcher'):
        print('[!] Kernel64Patcher not found, please install it')
        sys.exit(1)
    if not os.path.exists('/usr/local/bin/iBoot64Patcher'):
        print('[!] iBoot64Patcher not found, please install it')
        sys.exit(1)
    if not os.path.exists('/usr/local/bin/ldid'):
        print('[!] ldid not found, please install it')
        sys.exit(1)
    if not os.path.exists('/usr/local/bin/asr64_patcher'):
        print('[!] asr64_patcher not found, please install it')
        sys.exit(1)
    if not os.path.exists('/usr/local/bin/restored_external64_patcher'):
        print('[!] restored_external64_patcher not found, please install it')
        sys.exit(1)
    

def prep_restore(ipsw, blob, board, kpp, legacy):
    # extract the IPSW to the ./work directory
    print('[*] Extracting IPSW')
    with zipfile.ZipFile(ipsw, 'r') as z:
        z.extractall('./work')
    # make a directory in the work directory called ramdisk
    os.mkdir('./work/ramdisk')
    # read manifest from ./work/BuildManifest.plist
    with open('./work/BuildManifest.plist', 'rb') as f:
        manifest = Manifest(f.read())
    # get the ramdisk name
    ramdisk_path = manifest.get_comp(board, 'RestoreRamDisk')
    # extract it using img4
    print('[*] Extracting RamDisk')
    subprocess.run(['/usr/local/bin/img4', '-i', './work/' + ramdisk_path, '-o', './work/ramdisk.dmg'])
    # mount it using hdiutil
    print('[*] Mounting RamDisk')
    subprocess.run(['/usr/bin/hdiutil', 'attach', './work/ramdisk.dmg', '-mountpoint', './work/ramdisk'])
    # patch asr into the ramdisk
    print('[*] Patching ASR in the RamDisk')
    subprocess.run(['/usr/local/bin/asr64_patcher', './work/ramdisk/usr/sbin/asr', './work/patched_asr'])
    # extract the ents and save it to ./work/asr_ents.plist like:     subprocess.run(['/usr/local/bin/ldid', '-e', './work/ramdisk/usr/sbin/asr', '>', './work/asr.plist'])
    print('[*] Extracting ASR Ents')
    with open('./work/asr.plist', 'wb') as f:
        subprocess.run(['/usr/local/bin/ldid', '-e', './work/ramdisk/usr/sbin/asr'], stdout=f)
    # resign it using ldid
    print('[*] Resigning ASR')
    subprocess.run(['/usr/local/bin/ldid', '-S./work/asr.plist', './work/patched_asr'])
    # chmod 755 the new asr
    print('[*] Chmoding ASR')
    subprocess.run(['/bin/chmod', '-R', '755', './work/patched_asr'])
    # copy the patched asr back to the ramdisk
    print('[*] Copying Patched ASR back to the RamDisk')
    subprocess.run(['/bin/cp', './work/patched_asr', './work/ramdisk/usr/sbin/asr'])
    if not legacy:
        # patch restored_external 
        print('[*] Patching Restored External')
        subprocess.run(['/usr/local/bin/restored_external64_patcher' ,'./work/ramdisk/usr/local/bin/restored_external' ,'./work/restored_external_patched'])
        #resign it using ldid
        print('[*] Extracting Restored External Ents')
        with open('./work/restored_external.plist', 'wb') as f:
            subprocess.run(['/usr/local/bin/ldid', '-e', './work/ramdisk/usr/local/bin/restored_external'], stdout=f)
        # resign it using ldid
        print('[*] Resigning Restored External')
        subprocess.run(['/usr/local/bin/ldid', '-S./work/restored_external.plist', './work/restored_external_patched'])
        # chmod 755 the new restored_external
        print('[*] Chmoding Restored External')
        subprocess.run(['/bin/chmod', '-R', '755', './work/restored_external_patched'])
        # copy the patched restored_external back to the ramdisk
        print('[*] Copying Patched Restored External back to the RamDisk')
        subprocess.run(['/bin/cp', './work/restored_external_patched', './work/ramdisk/usr/local/bin/restored_external'])
    else:
        print('[*] Legacy mode, skipping restored_external')
    # detach the ramdisk
    print('[*] Detaching RamDisk')
    subprocess.run(['/usr/bin/hdiutil', 'detach', './work/ramdisk'])
    # create the ramdisk using pyimg4
    print('[*] Creating RamDisk')
    subprocess.run(['pyimg4', 'im4p', 'create', '-i', './work/ramdisk.dmg', '-o', './work/ramdisk.im4p', '-f', 'rdsk'])
    # get kernelcache name from manifest
    kernelcache = manifest.get_comp(board, 'RestoreKernelCache')
    # extract the kernel using pyimg4 like this: pyimg4 im4p extract -i kernelcache -o kcache.raw --extra kpp.bin 
    print('[*] Extracting Kernel')
    if kpp:
        subprocess.run(['pyimg4', 'im4p', 'extract', '-i', './work/' + kernelcache, '-o', './work/kcache.raw', '--extra', './work/kpp.bin'])
    else:
        subprocess.run(['pyimg4', 'im4p', 'extract', '-i', './work/' + kernelcache, '-o', './work/kcache.raw'])
    # patch the kernel using kernel64patcher like this: Kernel64Patcher kcache.raw krnl.patched -f -a
    print('[*] Patching Kernel')
    subprocess.run(['/usr/local/bin/kernel64patcher', './work/kcache.raw', './work/krnl.patched', '-f', '-a'])
    # rebuild the kernel like this: pyimg4 im4p create -i krnl.patched -o krnl.im4p --extra kpp.bin -f rkrn --lzss (leave out --extra kpp.bin if you dont have kpp)
    print('[*] Rebuilding Kernel')
    if kpp:
        subprocess.run(['pyimg4', 'im4p', 'create', '-i', './work/krnl.patched', '-o', './work/krnl.im4p', '--extra', './work/kpp.bin', '-f', 'rkrn', '--lzss'])
    else:
        subprocess.run(['pyimg4', 'im4p', 'create', '-i', './work/krnl.patched', '-o', './work/krnl.im4p', '-f', 'rkrn', '--lzss'])
    # done!
    print('[*] Done!')
    # ask user if they want to restore the device
    print('[?] Do you want to restore the device? (y/n)')
    if input() == 'y':
        # ask user if they are in pwndfu with sigchecks removed
        print('[?] Are you in pwndfu with sigchecks removed? (y/n)')
        if input() == 'y':
            # restore the device using futurestore like this: futurerestore -t blob --use-pwndfu --skip-blob --rdsk ramdisk.im4p --rkrn krnl.im4p --latest-sep --latest-baseband ipsw.ipsw
            print('[*] Restoring Device')
            subprocess.run(['/usr/local/bin/futurerestore', '-t', blob, '--use-pwndfu', '--skip-blob', '--rdsk', './work/ramdisk.im4p', '--rkrn', './work/krnl.im4p', '--latest-sep', '--latest-baseband', ipsw])
            # exit
            print('[*] Done!')
            # clean
            print('[*] Cleaning')
            subprocess.run(['/bin/rm', '-rf', './work'])
            print('[*] Done!')
            sys.exit(0)
        else:
            # dont restore device but tell user to enter pwndfu
            print('[!] You need to enter pwndfu')
            # tell the user how they can restore the device later
            print('[!] You can restore the device later using futurestore like this: futurerestore -t blob --use-pwndfu --skip-blob --rdsk ./work/ramdisk.im4p --rkrn ./work/krnl.im4p --latest-sep --latest-baseband ipsw.ipsw')
            # exit
            sys.exit(0)
    else:
        print('[*] Exiting')
        # clean up
        subprocess.run(['/bin/rm', '-rf', './work'])
        # exit
        sys.exit(0)

def prep_boot(ipsw, blob, board, kpp, identifier, legacy):
    # create a working directory
    print('[*] Creating Working Directory')
    subprocess.run(['/bin/mkdir', './work'])
    # unzip the ipsw
    print('[*] Unzipping IPSW')
    with zipfile.ZipFile(ipsw, 'r') as z:
        z.extractall('./work')
    with open('./work/BuildManifest.plist', 'rb') as f:
        manifest = Manifest(f.read())
    # get ProductBuildVersion from manifest
    print('[*] Getting ProductBuildVersion')
    productbuildversion = manifest.getProductBuildVersion()
    ibss_iv, ibss_key, ibec_iv, ibec_key = api.get_keys(identifier, board, productbuildversion)
    # get ibec and ibss from manifest
    print('[*] Getting IBSS and IBEC')
    ibss = manifest.get_comp(board, 'iBSS')
    ibec = manifest.get_comp(board, 'iBEC')
    # decrypt ibss like this:  img4 -i ibss -o ibss.dmg -k ivkey
    print('[*] Decrypting IBSS')
    subprocess.run(['/usr/local/bin/img4', '-i', './work/' + ibss, '-o', './work/ibss.dmg', '-k', ibss_iv + ibss_key])
    # decrypt ibec like this:  img4 -i ibec -o ibec.dmg -k ivkey
    print('[*] Decrypting IBEC')
    subprocess.run(['/usr/local/bin/img4', '-i', './work/' + ibec, '-o', './work/ibec.dmg', '-k', ibec_iv + ibec_key])
    # patch ibss like this:  iBoot64Patcher ibss.dmg ibss.patched
    print('[*] Patching IBSS')
    subprocess.run(['/usr/local/bin/iBoot64Patcher', './work/ibss.dmg', './work/ibss.patched'])
    # patch ibec like this:  iBoot64Patcher ibec.dmg ibec.patched -b "-v"
    print('[*] Patching IBEC')
    subprocess.run(['/usr/local/bin/iBoot64Patcher', './work/ibec.dmg', './work/ibec.patched', '-b', '-v'])
    # convert blob into im4m like this: img4tool -e -s blob -m IM4M
    print('[*] Converting BLOB to IM4M')
    subprocess.run(['/usr/local/bin/img4tool', '-e', '-s', blob, '-m', 'IM4M'])
    # convert ibss into img4 like this:  img4 -i ibss.patched -o ibss.img4 -M IM4M -A -T ibss
    print('[*] Converting IBSS to IMG4')
    subprocess.run(['/usr/local/bin/img4', '-i', './work/ibss.patched', '-o', './work/ibss.img4', '-M', 'IM4M', '-A', '-T', 'ibss'])
    # convert ibec into img4 like this:  img4 -i ibec.patched -o ibec.img4 -M IM4M -A -T ibec
    print('[*] Converting IBEC to IMG4')
    subprocess.run(['/usr/local/bin/img4', '-i', './work/ibec.patched', '-o', './work/ibec.img4', '-M', 'IM4M', '-A', '-T', 'ibec'])
    # get the names of the devicetree and trustcache
    print('[*] Getting Device Tree and TrustCache')
    # read manifest from ./work/BuildManifest.plist
    if legacy:
        devicetree = manifest.get_comp(board, 'DeviceTree')
    else:
        trustcache = manifest.get_comp(board, 'StaticTrustCache')
        devicetree = manifest.get_comp(board, 'DeviceTree')
    # sign them like this  img4 -i devicetree -o devicetree.img4 -M IM4M -T rdtr
    print('[*] Signing Device Tree')
    subprocess.run(['/usr/local/bin/img4', '-i', './work/' + devicetree, '-o', './work/devicetree.img4', '-M', 'IM4M', '-T', 'rdtr'])
    # sign them like this   img4 -i trustcache -o trustcache.img4 -M IM4M -T rtsc
    print('[*] Signing Trust Cache')
    if not legacy:
        subprocess.run(['/usr/local/bin/img4', '-i', './work/' + trustcache, '-o', './work/trustcache.img4', '-M', 'IM4M', '-T', 'rtsc'])
    # grab kernelcache from manifest
    print('[*] Getting Kernel Cache')
    kernelcache = manifest.get_comp(board, 'KernelCache')
    # extract the kernel like this:  pyimg4 im4p extract -i kernelcache -o kcache.raw --extra kpp.bin 
    print('[*] Extracting Kernel')
    if kpp:
        subprocess.run(['pyimg4', 'im4p', 'extract', '-i', './work/' + kernelcache, '-o', './work/kcache.raw', '--extra', './work/kpp.bin'])
    else:
        subprocess.run(['pyimg4', 'im4p', 'extract', '-i', './work/' + kernelcache, '-o', './work/kcache.raw'])
    # patch it like this:   Kernel64Patcher kcache.raw krnlboot.patched -f
    print('[*] Patching Kernel')
    subprocess.run(['/usr/local/bin/Kernel64Patcher', './work/kcache.raw', './work/krnlboot.patched', '-f'])
    # convert it like this:   pyimg4 im4p create -i krnlboot.patched -o krnlboot.im4p --extra kpp.bin -f rkrn --lzss
    print('[*] Converting Kernel')
    if kpp:
        subprocess.run(['pyimg4', 'im4p', 'create', '-i', './work/krnlboot.patched', '-o', './work/krnlboot.im4p', '--extra', './work/kpp.bin', '-f', 'rkrn', '--lzss'])
    else:
        subprocess.run(['pyimg4', 'im4p', 'create', '-i', './work/krnlboot.patched', '-o', './work/krnlboot.im4p', '-f', 'rkrn', '--lzss'])
    # sign it like this:  pyimg4 img4 create -p krnlboot.im4p -o krnlboot.img4 -m IM4M
    print('[*] Signing Kernel')
    subprocess.run(['pyimg4', 'img4', 'create', '-p', './work/krnlboot.im4p', '-o', './work/krnlboot.img4', '-m', 'IM4M'])
    # create boot directory
    print('[*] Creating Boot Directory')
    subprocess.run(['mkdir', './boot'])
    # copy ibss, ibec, trustcache, devicetree, and krnlboot to the boot directory
    print('[*] Copying files to boot directory')
    subprocess.run(['cp', './work/ibss.img4', './boot/ibss.img4'])
    subprocess.run(['cp', './work/ibec.img4', './boot/ibec.img4'])
    if not legacy:
        subprocess.run(['cp', './work/trustcache.img4', './boot/trustcache.img4'])
    subprocess.run(['cp', './work/devicetree.img4', './boot/devicetree.img4'])
    subprocess.run(['cp', './work/krnlboot.img4', './boot/krnlboot.img4'])
    # clean up
    print('[*] Cleaning up')
    subprocess.run(['rm', '-rf', './work'])
    print('[*] Done!')
    # done
    print('[*] Done!')
    print('[*] Boot using:  ./boot.sh')
    sys.exit(0)


def main():
    dependencies()
    parser = argparse.ArgumentParser(description='iOS Tethered IPSW Restore')
    parser.add_argument('-i', '--ipsw', help='IPSW to restore', required=True)
    parser.add_argument('-t', '--blob', help='Blob to use', required=True)
    parser.add_argument('-r', '--restore', help='Restore Mode', required=False)
    parser.add_argument('-b', '--boot', help='Boot Mode', required=False)
    parser.add_argument('-d', '--boardconfig', help='BoardConfig to use', required=True)
    parser.add_argument('-kpp', '--kpp', help='Use KPP', required=False)
    parser.add_argument('-id', '--identifier', help='Identifier to use', required=False)
    parser.add_argument('--legacy', help='Use Legacy Mode (ios 11 or lower)', required=False)
    args = parser.parse_args()
    if args.restore:
        prep_restore(args.ipsw, args.blob, args.boardconfig, args.kpp, args.legacy)
    elif args.boot:
        if args.identifier == None:
            print('[!] You need to specify an identifier')
            sys.exit(0)
        prep_boot(args.ipsw, args.blob, args.boardconfig, args.kpp, args.identifier, args.legacy)
    else:
        print('[!] Please specify a mode')
        sys.exit(0)

if __name__ == '__main__':
    print("sunst0rm")
    print("Made by mineek")
    print("Some code by m1n1exploit")
    main()
