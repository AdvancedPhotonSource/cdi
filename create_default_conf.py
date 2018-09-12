import argparse
import sys
import aps_34id.prep as prep


def main(arg):
    parser = argparse.ArgumentParser()
    parser.add_argument("working_dir", help="working directory")
    parser.add_argument("id", help="name of the experiment/data reconstruction")

    args = parser.parse_args()

    prep.create_default_config(args.working_dir, args.id)


if __name__ == "__main__":
        main(sys.argv[1:])

# python create_default_config.py '/home/beams/CXDUSER/CDI/cdi-master/test', 'A_48-60'
