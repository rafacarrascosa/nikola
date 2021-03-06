import os

try:
    import webassets
except ImportError:
    webassets = None  # NOQA

from nikola.plugin_categories import LateTask
from nikola import utils


class BuildBundles(LateTask):
    """Bundle assets using WebAssets."""

    name = "build_bundles"

    def set_site(self, site):
        super(BuildBundles, self).set_site(site)
        if webassets is None:
            self.site.config['USE_BUNDLES'] = False

    def gen_tasks(self):
        """Bundle assets using WebAssets."""

        kw = {
            'filters': self.site.config['FILTERS'],
            'output_folder': self.site.config['OUTPUT_FOLDER'],
            'cache_folder': self.site.config['CACHE_FOLDER'],
            'theme_bundles': get_theme_bundles(self.site.THEMES),
        }

        def build_bundle(output, inputs):
            out_dir = os.path.join(kw['output_folder'], os.path.dirname(output))
            inputs = [i for i in inputs if os.path.isfile(
                os.path.join(out_dir, i))]
            cache_dir = os.path.join(kw['cache_folder'], 'webassets')
            if not os.path.isdir(cache_dir):
                os.makedirs(cache_dir)
            env = webassets.Environment(out_dir, os.path.dirname(output),
                cache=cache_dir)
            bundle = webassets.Bundle(*inputs,
                output=os.path.basename(output))
            env.register(output, bundle)
            # This generates the file
            env[output].urls()

        flag = False
        if webassets is not None and self.site.config['USE_BUNDLES'] is not False:
            for name, files in kw['theme_bundles'].items():
                output_path = os.path.join(kw['output_folder'], name)
                dname = os.path.dirname(name)
                file_dep = [os.path.join('output', dname, fname)
                    for fname in files]
                task = {
                    'file_dep': file_dep,
                    'basename': self.name,
                    'name': output_path,
                    'actions': [(build_bundle, (name, files))],
                    'targets': [output_path],
                    'uptodate': [utils.config_changed(kw)]
                    }
                flag = True
                yield utils.apply_filters(task, kw['filters'])
        if flag is False:  # No page rendered, yield a dummy task
            yield {
                'basename': self.name,
                'uptodate': [True],
                'name': 'None',
                'actions': [],
            }


def get_theme_bundles(themes):
    """Given a theme chain, return the bundle definitions."""
    bundles = {}
    for theme_name in themes:
        bundles_path = os.path.join(
            utils.get_theme_path(theme_name), 'bundles')
        if os.path.isfile(bundles_path):
            with open(bundles_path) as fd:
                for line in fd:
                    name, files = line.split('=')
                    files = [f.strip() for f in files.split(',')]
                    bundles[name.strip()] = files
                break
    return bundles
