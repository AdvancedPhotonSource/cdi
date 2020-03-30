import reccdi.bin.run_prep_34idc as prep
import reccdi.bin.format_data as dt
import reccdi.bin.run_rec as rec
import reccdi.bin.run_disp as dsp
import sys
import argparse

def run_all(dev, experiment_dir, **kwargs):
    prep.set_prep(experiment_dir)
    dt.data(experiment_dir)
    if 'rec_id' in kwargs:
        rec.manage_reconstruction(dev, experiment_dir, kwargs['rec_id'])
    else:
        rec.manage_reconstruction(dev, experiment_dir)
    if 'results_dir' in kwargs:
        dsp.to_vtk(experiment_dir, kwargs['results_dir'])
    else:
        dsp.to_vtk(experiment_dir)

def main(arg):
    parser = argparse.ArgumentParser()
    parser.add_argument("dev", help="processor to run on (cpu, opencl, cuda)")
    parser.add_argument("experiment_dir", help="experiment directory")
    parser.add_argument("--rec_id", help="reconstruction id, a prefix to '_results' directory")
    parser.add_argument("--results_dir", help="directory in experiment that has a tree (or leaf) with reconstruction results which will be visualized")

    args = parser.parse_args()
    dev = args.dev
    experiment_dir = args.experiment_dir
    run_all(dev, experiment_dir, rec_id=args.rec_id, results_dir=args.results_dir)


if __name__ == "__main__":
    main(sys.argv[1:])

