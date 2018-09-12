import argparse
import sys
import aps_34id.prep as prep


def main(arg):
    parser = argparse.ArgumentParser()
    parser.add_argument("working_dir", help="working directory")
    parser.add_argument("id", help="name of the experiment/data reconstruction")
    parser.add_argument("scan", help="a range of scans to prepare data from")
    parser.add_argument("data_dir", help="directory where the scan data is collected")
    parser.add_argument("specfile", help="spec file saved during experiment")
    parser.add_argument("darkfile", help="file containing dark data")
    parser.add_argument("whitefile", help="file containing white data")

    args = parser.parse_args()
    scan = args.scan
    try:
        # convert it to list of int
        scan_range = scan.split('-')
        scan_num = []
        for i in range(len(scan_range)):
            scan_num.append(int(scan_range[i]))
    except:
        print ('enter numeric values for scan range')

    prep.prepare(args.working_dir, args.id, scan_num, args.data_dir, args.specfile, args.darkfile, args.whitefile)


if __name__ == "__main__":
        main(sys.argv[1:])

# python run_prepare.py '/home/beams/CXDUSER/CDI/cdi-master/test'
#  'A_48-60'
#  '48-60'
#  '/net/s34data/export/34idc-data/2018/Startup18-2/ADStartup18-2a'
#  '/net/s34data/export/34idc-data/2018/Startup18-2/Startup18-2a.spec'
#  '/net/s34data/export/34idc-work/2018/Startup18-2/dark.tif'
#  '/net/s34data/export/34idc-work/2018/Startup18-2/CelaWhiteField.tif'