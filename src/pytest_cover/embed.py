"""Activate coverage at python startup if appropriate.

The python site initialisation will ensure that anything we import
will be removed and not visible at the end of python startup.  However
we minimise all work by putting these init actions in this separate
module and only importing what is needed when needed.

For normal python startup when coverage should not be activated the pth
file checks a single env var and does not import or call the init fn
here.

For python startup when an ancestor process has set the env indicating
that code coverage is being collected we activate coverage based on
info passed via env vars.
"""
import os


def multiprocessing_start(obj):
    cov = init()
    multiprocessing.util.Finalize(None, multiprocessing_finish, args=(cov,), exitpriority=1000)


def multiprocessing_finish(cov):
    cov.stop()
    cov.save()


try:
    import multiprocessing.util
except ImportError:
    pass
else:
    multiprocessing.util.register_after_fork(multiprocessing_start, multiprocessing_start)


def init():
    # Only continue if ancestor process has set everything needed in
    # the env.

    cov_source = os.environ.get('COV_CORE_SOURCE')
    cov_config = os.environ.get('COV_CORE_CONFIG')
    if cov_config:
        # Import what we need to activate coverage.
        import coverage

        # Determine all source roots.
        if not cov_source:
            cov_source = None
        else:
            cov_source = cov_source.split(os.pathsep)

        # Activate coverage for this process.
        cov = coverage.coverage(source=cov_source,
                                data_suffix=True,
                                config_file=cov_config,
                                auto_data=True)
        cov.erase()
        cov.start()
        return cov