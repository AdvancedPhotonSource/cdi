import sys
import reccdi.src_py.beamlines.aps_34id.setup_34idc as prep

if __name__ == "__main__":
    prep.main(sys.argv[1:])
    #exit(prep.main(sys.argv[1:]))

# python run_prepare.py prefix scans conf_dir
