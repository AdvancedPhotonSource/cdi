import sys
import reccdi.src_py.run_scripts.run_34id_prepare as prep

if __name__ == "__main__":
    exit(prep.main(sys.argv[1:]))

# python run_prepare.py prefix scans conf_dir
