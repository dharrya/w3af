'''
phishingVector.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''
from __future__ import with_statement

import re
from lxml import etree

import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
from core.data.fuzzer.fuzzer import createMutants

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity


class phishingVector(baseAuditPlugin):
    '''
    Find phishing vectors.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        # Some internal vars
        self._tag_xpath = etree.XPath('//iframe | //frame')
        
        # I test this with different URL handlers because the developer may have
        # blacklisted http:// and https:// but missed ftp://.
        #
        # I also use hTtp instead of http because I want to evade some (stupid) 
        # case sensitive filters
        self._test_urls = ('hTtp://w3af.sf.net/', 'htTps://w3af.sf.net/',
                           'fTp://w3af.sf.net/')

    def audit(self, freq ):
        '''
        Find those phishing vectors!
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'phishingVector plugin is testing: ' + freq.getURL() )
        
        mutants = createMutants( freq , self._test_urls )
        for mutant in mutants:
            args = (mutant,)
            kwds = {'callback': self._analyze_result }
            self._run_async(meth=self._uri_opener.send_mutant, args=args,
                                                                kwds=kwds)
        self._join()
            
    def _analyze_result(self, mutant, response):
        '''
        Analyze results of the _send_mutant method.
        '''
        with self._plugin_lock:
            if self._has_no_bug(mutant):
                    vulns = self._find_phishing_vector(mutant, response)
                    for vuln in vulns:
                        kb.kb.append(self, 'phishingVector', vuln)
    
    def _find_phishing_vector( self, mutant, response ):
        '''
        Find the phishing vectors!
        '''
        dom = response.getDOM()
        
        if response.is_text_or_html() and dom is not None:

            res = []
            elem_list = self._tag_xpath( dom )
            
            for element in elem_list:

                if 'src' not in element.attrib:
                    return []
                
                src_attr = element.attrib['src']
                
                for url in self._test_urls:
                    if src_attr.startswith( url ):
                        # Vuln vuln!
                        v = vuln.vuln( mutant )
                        v.setPluginName(self.getName())
                        v.setId( response.id )
                        v.setSeverity(severity.LOW)
                        v.setName( 'Phishing vector' )
                        v.setDesc( 'A phishing vector was found at: ' + mutant.foundAt() )
                        v.addToHighlight( src_attr )
                        res.append( v )
                        
            return res
        
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._join()
        self.printUniq( kb.kb.getData( 'phishingVector', 'phishingVector' ), 'VAR' )

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def setOptions( self, OptionList ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return []
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugins finds phishing vectors in web applications, for example, a bug of this type is found
        if I request the URL "http://site.tld/asd.asp?info=http://attacker.tld" and in the response
        HTML the web application sends: 
            ... 
            <iframe src="http://attacker.tld">
            ....
        '''
