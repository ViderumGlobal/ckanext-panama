import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as lib_helpers
from ckan.lib.plugins import DefaultTranslation

from ckanext.scheming.plugins import (SchemingGroupsPlugin,
                                      SchemingOrganizationsPlugin)

import ckanext.panama.helpers as panama_helpers
from ckanext.panama.auth import send_contact


import logging
log = logging.getLogger(__name__)


def _fluent_to_core_fields(dic, fluent_core_field_map):
    '''Update the core field value in the dic with the mapped fluent
    field value in the current language, or of the default locale.'''

    def add_to_dict(d, field_map):
        fluent_field = d.get(field_map[0])
        if fluent_field and type(fluent_field) is dict:
            current_lang = lib_helpers.lang()
            if fluent_field.get(current_lang):
                d[field_map[1]] = fluent_field[current_lang]
            else:
                d[field_map[1]] = \
                    fluent_field[panama_helpers.get_default_locale()]
        return d

    for field_map in fluent_core_field_map:
        # for packages and groups
        add_to_dict(dic, field_map)

        # for resources (if present)
        if dic.get('resources'):
            for res_dict in dic['resources']:
                add_to_dict(res_dict, field_map)

    return dic


class PanamaPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITranslation)


    # mapping between fluent field and core field
    fluent_core_field_map = [('fluent_title', 'title'),
                             ('fluent_notes', 'notes'),
                             ('fluent_name', 'name'),
                             ('fluent_description', 'description')]

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'panama')

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'get_default_locale': panama_helpers.get_default_locale,
            'get_extra_exclude_fields':
                panama_helpers.get_extra_exclude_fields,
            'get_recently_updated_panama_datasets':
                panama_helpers.get_recently_updated_panama_datasets,
            'panama_get_group_fluent_name':
                panama_helpers.panama_get_group_fluent_name,
            'panama_get_groups_len':
                panama_helpers.panama_get_groups_len
        }

    def before_index(self, pkg_dict):
        pkg_dict = _fluent_to_core_fields(pkg_dict, self.fluent_core_field_map)
        return pkg_dict

    def before_view(self, pkg_dict):
        return _fluent_to_core_fields(pkg_dict, self.fluent_core_field_map)

    def after_show(self, context, pkg_dict):
        return _fluent_to_core_fields(pkg_dict, self.fluent_core_field_map)



class PanamaGroupPlugin(plugins.SingletonPlugin):

    '''Ensure grp_dict['display_name'] is using the correct language.'''

    plugins.implements(plugins.IGroupController, inherit=True)

    # mapping between fluent field and core field
    fluent_core_field_map = [('fluent_title', 'display_name'),
                             ('fluent_description', 'description')]

    def before_view(self, grp_dict):
        grp = toolkit.get_action('group_show')(
            data_dict={'id': grp_dict['id']})
        grp = _fluent_to_core_fields(grp, self.fluent_core_field_map)
        grp_dict['display_name'] = grp['display_name']
        grp_dict['description'] = grp['description']

        return grp_dict


class PanamaOrganizationPlugin(plugins.SingletonPlugin):

    '''Ensure grp_dict['display_name'] is using the correct language.'''

    plugins.implements(plugins.IOrganizationController, inherit=True)

    # mapping between fluent field and core field
    fluent_core_field_map = [('fluent_title', 'display_name'),
                             ('fluent_description', 'description')]

    def before_view(self, grp_dict):
        grp = toolkit.get_action('organization_show')(
            data_dict={'id': grp_dict['id']})
        grp = _fluent_to_core_fields(grp, self.fluent_core_field_map)
        grp_dict['display_name'] = grp['display_name']
        grp_dict['description'] = grp['description']

        return grp_dict


class PanamaSchemingGroupsPlugin(SchemingGroupsPlugin):

    def about_template(self):
        return 'group/about.html'


class PanamaSchemingOrganizationsPlugin(SchemingOrganizationsPlugin):

    def about_template(self):
        return 'organization/about.html'


class PanamaContactPlugin(plugins.SingletonPlugin):
    """
    CKAN Contact Extension
    This is modified version of ckanext-contact that can be found on:
    https://github.com/NaturalHistoryMuseum/ckanext-contact
    """
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IAuthFunctions)

    ## IRoutes
    def before_map(self, map):

        # Add controller for KE EMu specimen records
        map.connect('contact_form', '/contact',
                    controller='ckanext.panama.controllers.contact:ContactController',
                    action='form')

        # Add AJAX request handler
        map.connect('contact_ajax_submit', '/contact/ajax',
                    controller='ckanext.panama.controllers.contact:ContactController',
                    action='ajax_submit')

        return map

    ## IAuthFunctions
    def get_auth_functions(self):
        return {'send_contact': send_contact}

