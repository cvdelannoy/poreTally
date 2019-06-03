from ete3 import NCBITaxa
from helper_functions import is_integer
import os
import yaml

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
ncbi = NCBITaxa()
# ncbi.update_taxonomy_database()


class Metadata(object):
    """ A class for storing metadata on poreTally runs

    """
    def __init__(self, user_info_dict):
        self.ncbi = NCBITaxa()
        self.authors = user_info_dict['authors']
        self.species_name = user_info_dict['species']
        self.taxid = user_info_dict['species']
        self.flowcell = user_info_dict['flowcell']
        self.kit = user_info_dict['kit']
        self.basecaller = user_info_dict['basecaller']

    def write_publication_info(self, fn):
        out_dict = {
            'authors': self.authors,
            'species_name': self.species_name,
            'taxid': self.taxid,
            'flowcell': self.flowcell,
            'kit': self.kit,
            'basecaller': self.basecaller
        }
        with open(fn, 'w') as fn_handle:
            yaml.dump(out_dict, fn_handle, default_flow_style=False)

    @property
    def is_eukaryote(self):
        if ncbi.get_lineage(self.taxid)[2] == 2759:
            return True
        else:
            return False

    @property
    def species_name(self):
        return self._species_name

    @property
    def taxid(self):
        return self._taxid

    @property
    def flowcell(self):
        return self._flowcell

    @property
    def kit(self):
        return self._kit

    @species_name.setter
    def species_name(self, species):
        if is_integer(species):
            ncbi_dict = ncbi.get_taxid_translator([species])
            if ncbi_dict:
                self._species_name = ncbi_dict[species][0]
            else:
                self._species_name = None
        elif type(species) is str:
            self._species_name = species
        else:
            raise ValueError('species should be string or int')

    @taxid.setter
    def taxid(self, species):
        if is_integer(species):
            self._taxid = int(species)
        elif type(species) is str:
            ncbi_dict = ncbi.get_name_translator([species])
            if ncbi_dict:
                self._taxid = ncbi_dict[species][0]
            else:
                self._taxid = None
        else:
            raise ValueError('species should be string or int')

    @flowcell.setter
    def flowcell(self, flowcell):
        with open(__location__+'/allowed_publication_info_names.yaml', 'r') as f:
            allowed_names = yaml.full_load(f)
        if flowcell not in allowed_names['flowcell']:
            flowcell_list = ', '.join(allowed_names['flowcell'])
            raise ValueError('{fc} is not a valid flowcell name, '
                             'must be one of: {fc_list}'.format(fc=flowcell,
                                                                fc_list= flowcell_list))
        self._flowcell = flowcell

    @kit.setter
    def kit(self, kit):
        with open(__location__+'/allowed_publication_info_names.yaml', 'r') as f:
            allowed_names = yaml.full_load(f)
        if kit not in allowed_names['kit']:
            kit_list = ', '.join(allowed_names['kit'])
            raise ValueError('{kt} is not a valid flowcell name, '
                             'must be one of: {kt_list}'.format(kt=kit,
                                                                kt_list=kit_list))
        self._kit = kit
