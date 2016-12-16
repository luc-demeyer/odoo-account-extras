# -*- coding: utf-8 -*-

##############################################################################
#
# Tidy Partner column of Journals legal report
# Copyright (C) 2016 OpusVL (<http://opusvl.com/>)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'Tidy Partner column of Journals legal report',
    'version': '0.1',
    'author': 'OpusVL',
    'website': 'http://opusvl.com/',
    'summary': 'Remove res.partner() from Partner column on Accounting -> Reporting -> Legal Reports -> Journals -> Journals',
    
    'category': 'Accounting',
    
    'description': """Remove res.partner() from Partner column on Accounting -> Reporting -> Legal Reports -> Journals -> Journals,
""",
    'images': [
    ],
    'depends': [
        'account',
    ],
    'data': [
        'views/account_report_journal.xml',
    ],
    'demo': [
    ],
    'test': [
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
