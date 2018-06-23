# -*- coding: utf-8 -*-
"""
    femagtools.grid
    ~~~~~~~~~~~~~~~

    Parameter range calculation



"""
import logging
import glob
import os
import numpy as np
import femagtools
import femagtools.model
import femagtools.fsl
import femagtools.condor
import femagtools.moproblem
import shutil

logger = logging.getLogger(__name__)


def baskets(items, basketsize=10):
    """generates balanced baskets from iterable, contiguous items"""
    num_items = len(items)
    num_baskets = max(1, num_items//basketsize)
    if num_items % basketsize and basketsize < num_items:
        num_baskets += 1
    step = num_items//num_baskets
    for i in range(0, num_items, step):
        yield items[i:i+step]


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i+n]


def create_parameter_range(domain):
    """returns the transposed array of the combined domain values"""
    L = [len(d) for d in domain]
    LS = np.prod(L)
    s = []
    e = 1
    for d in domain:
        LS = LS//len(d)
        s.append(np.repeat(d*LS, e))
        e = e*L[0]
        L = L[1:]
    return np.array(s).T


class Grid(object):
    """Parameter variation calculation"""
    def __init__(self, workdir,
                 magnetizingCurves=None, magnets=None):
        self.femag = femagtools.Femag(workdir,
                                      magnetizingCurves=magnetizingCurves,
                                      magnets=magnets)
        self.stop = False  # rudimentary: gives the ability to stop a running parameter variation. thomas.maier/OSWALD
        self.reportdir=''
        """
        the "owner" of the Grid have to take care to terminate all running xfemag64 or wfemagw64
        processes after setting stop to True
        For example:
        
        def killFemagThreads():
            if sys.platform.startswith('linux'):
                os.system("kill $(ps aux | grep '[x]femag64' | awk '{print $2}')")
            else:
                os.system("taskkill /f /im wfemagw64.exe")
                
        thomas.maier/OSWALD
        """

    def set_report_directory(self, dirname):
        """saves the result files (BCH/BATCH) of every calculation 
        into this directory. Throws ValueError if directory is not empty or 
        FileNotFoundError if it does not exist.
        Args:
          dirname: name of report directory
        """
        if os.listdir(dirname):
            raise ValueError("directory {} is not empty".format(dirname))
        self.reportdir = dirname

        
    def setup_model(self, builder, model):
        """builds model in current workdir and returns its filenames"""
        # get and write mag curves
        mc_files = self.femag.copy_magnetizing_curves(model)
        
        filename = 'femag.fsl'
        logger.info("setup model in %s", self.femag.workdir)
        with open(os.path.join(self.femag.workdir, filename), 'w') as f:
            f.write('\n'.join(builder.create_model(model,
                                                   self.femag.magnets) +
                              ['save_model(close)']))

        self.femag.run(filename, options=['-b'])
        model_files = [os.path.join(self.femag.workdir, m)
                       for m in mc_files] + \
                           glob.glob(os.path.join(self.femag.workdir,
                                                  model.name+'_*.poc')) + \
                            glob.glob(os.path.join(self.femag.workdir,
                                                   model.name+'*7'))
        
        logger.info("model %s created", model.name)
        return model_files
    
    def __call__(self, opt, pmMachine, operatingConditions,
                 engine, bchMapper=None):
        """calculate objective vars for all decision vars"""

        self.stop = False  # make sure the calculation will start. thomas.maier/OSWALD

        decision_vars = opt['decision_vars']
        objective_vars = opt.get('objective_vars', {})

        steps = [d.get('steps', 10) for d in decision_vars]
        logger.info('STEPS %s', str(steps))

        model = femagtools.model.MachineModel(pmMachine)
        # check if this model needs to be modified
        immutable_model = len([d for d in decision_vars
                               if hasattr(model,
                                          d['name'].split('.')[0])]) == 0
        operatingConditions['lfe'] = model.lfe
        operatingConditions['move_action'] = model.move_action
        operatingConditions['pocfilename'] = (model.get('name') +
                                              '_' + str(model.get('poles')) +
                                              'p.poc')
        operatingConditions.update(model.windings)
        fea = femagtools.model.FeaModel(operatingConditions)

        prob = femagtools.moproblem.FemagMoProblem(decision_vars,
                                                   objective_vars)

        job = engine.create_job(self.femag.workdir)
        builder = femagtools.fsl.Builder()

        # build x value array
        
        domain = [list(np.linspace(l, u, s))
                  for s, l, u in zip(steps, prob.lower, prob.upper)]

        par_range = create_parameter_range(domain)
        f = []
        p = 1
        calcid = 0
        logger.debug(par_range)

        if immutable_model:
            modelfiles = self.setup_model(builder, model)
            logger.info("Files %s", modelfiles)

        self.bchmapper_data = []  # clear bch data
        # split x value (par_range) array in handy chunks:
        for population in baskets(par_range, opt['population_size']):
            if self.stop:  # try to return the results so far. thomas.maier/OSWALD
                logger.info(
                    'stopping grid execution... returning results so far...')
                try:
                    shape = [len(objective_vars)] + [len(d)
                                                     for d in reversed(domain)]
                    logger.debug("BEFORE: f shape %s --> %s",
                                 np.shape(np.array(f).T), shape)
                    completed = int(reduce((lambda x, y: x * y),
                                           [len(z) for z in domain]))
                    logger.debug("need {} in total".format(completed))
                    remaining = completed - int(np.shape(np.array(f).T)[1])
                    values = int(np.shape(np.array(f).T)[0])
                    logger.debug("going to append {} None values".format(
                        remaining))
                    f += remaining * [values * [np.nan]]
                    shape = [len(objective_vars)] + [len(d)
                                                     for d in reversed(domain)]
                    logger.debug("AFTER: f shape %s --> %s",
                                 np.shape(np.array(f).T), shape)
                    objectives = np.reshape(np.array(f).T, shape)
                    r = dict(f=objectives.tolist(),
                             x=domain)
                    return r
                except:
                    return {}
                    pass

            logger.info('........ %d / %d', p, len(par_range)//len(population))
            job.cleanup()
            for k, x in enumerate(population):
                task = job.add_task()
                if immutable_model:
                    prob.prepare(x, fea)
                    for m in modelfiles:
                        task.add_file(m)
                    task.add_file('femag.fsl',
                                  builder.create_open(model) +
                                  builder.create_common(model) +
                                  builder.create_analysis(fea))
                else:
                    try:
                        prob.prepare(x, model)
                    except:
                        prob.prepare(x, [model, fea])
                    logger.info("prepare %s", x)
                    for mc in self.femag.copy_magnetizing_curves(
                            model,
                            task.directory):
                        task.add_file(mc)

                    task.add_file('femag.fsl',
                                  builder.create_model(model,
                                                       self.femag.magnets) +
                                  builder.create_analysis(fea))

            status = engine.submit()
            logger.info('Started %s', status)
            if bchMapper and isinstance(engine, femagtools.condor.Engine):
                return {}  # BatchCalc Mode
            status = engine.join()

            for t in job.tasks:
                if t.status == 'C':
                    r = t.get_results()
                    # save result file if requested:
                    if self.reportdir:
                        repdir = os.path.join(self.reportdir,
                                              str(calcid))
                        os.makedirs(repdir)
                        try:
                            shutil.copy(glob.glob(os.path.join(
                                t.directory, r.filename)+'.B*CH')[0], repdir)
                        except FileNotFoundError:
                            pass
                        calcid += 1
                    if bchMapper:  # Mode => collectBchData
                        self.addBchMapperData(bchMapper(r))
                    if isinstance(r, dict) and 'error' in r:
                        logger.warn("job %d failed: %s", k, r['error'])
                        f.append([float('nan')]*len(objective_vars))
                    else:
                        prob.setResult(bchMapper(r)) if bchMapper else prob.setResult(r)

                        f.append(prob.objfun([]))
            p += 1

        logger.info('...... DONE')
        logger.debug("Result %s", np.shape(f))

        shape = [len(objective_vars)] + [len(d) for d in reversed(domain)]
        logger.info("f shape %s --> %s", np.shape(np.array(f).T), shape)
        objectives = np.reshape(np.array(f).T, shape)
        if self.reportdir:
            self._write_report(decision_vars, objective_vars,
                               objectives, domain)
        return dict(f=objectives.tolist(),
                    x=domain)

    def addBchMapperData(self, bchData):
        self.bchmapper_data.append(bchData)

    def getBchMapperData(self):
        return self.bchmapper_data

    def _write_report(self, decision_vars, objective_vars, objectives, domain):
        with open(os.path.join(self.reportdir, 'grid-report.csv'), 'w') as f:
            f.write(';'.join([d['label']
                              for d in decision_vars] +
                              [o['label']
                               for o in objective_vars] + ['Directory']))
            f.write('\n')
            f.write(';'.join([d['name']
                              for d in decision_vars] +
                              [o['name']
                               for o in objective_vars]))
            f.write('\n')
            # print values in table format
            calcid = 0
            x = create_parameter_range(domain)
            y = np.reshape(objectives, (np.shape(objectives)[0],
                                        np.shape(x)[0])).T
            for l in np.hstack((x, y)):
                f.write(';'.join(['{}'.format(z) for z in l] +
                                 [str(calcid)]))
                f.write('\n')
                calcid += 1
