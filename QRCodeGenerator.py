#   
# Gramps - a GTK+/GNOME based genealogy program - Family Sheet plugin
#
# Copyright (C) 2008,2009,2010 Reinhard Mueller
# Copyright (C) 2010 Jakim Friant
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# $Id$

"""Reports/Text Reports/QRCodeGenerator"""

from __future__ import unicode_literals

#------------------------------------------------------------------------
#
# Standard Python modules
#
#------------------------------------------------------------------------
import string

#------------------------------------------------------------------------
#
# GRAMPS modules
#  
#------------------------------------------------------------------------
import qrcode
import StringIO
from gramps.gen.display.name import displayer
from gramps.gen.lib import Date, Event, EventType, FamilyRelType, Name
from gramps.gen.lib import StyledText, StyledTextTag, StyledTextTagType
from gramps.gen.plug import docgen
from gramps.gen.plug.menu import BooleanOption, EnumeratedListOption, PersonOption
from gramps.gen.plug.menu import FilterOption
from gramps.gen.plug.report import Report
from gramps.gen.plug.report import utils
from gramps.gen.plug.report import MenuReportOptions
import gramps.gen.datehandler
from gramps.gen.relationship import get_relationship_calculator
from gramps.gen.const import GRAMPS_LOCALE as glocale
try:
    _trans = glocale.get_addon_translator(__file__)
except ValueError:
    _trans = glocale.translation
_ = _trans.gettext

#------------------------------------------------------------------------
#
# Constants
#
#------------------------------------------------------------------------
empty_birth = Event()
empty_birth.set_type(EventType.BIRTH)

empty_marriage = Event()
empty_marriage.set_type(EventType.MARRIAGE)


#------------------------------------------------------------------------
#
# Relations report
#
#------------------------------------------------------------------------
class QRCodeGenerator(Report):
    """
    QRCodeGenerator is a page that contains the name and QRCodes related to a family or an event.   
    """

    def __init__(self, database, options, user):
        """
        Initialize the report.

        @param database: the GRAMPS database instance
        @param options: instance of the Options class for this report
        @param user: a gramps.gen.user.User() instance
        """

        Report.__init__(self, database, options, user)
        menu = options.menu
        self.person_id    = menu.get_option_by_name('pid').get_value()
        self.person2_id   = menu.get_option_by_name('pid2').get_value()
        self.recurse      = menu.get_option_by_name('recurse').get_value()
        self.callname     = menu.get_option_by_name('callname').get_value()
        self.placeholder  = menu.get_option_by_name('placeholder').get_value()
        self.incl_sources = menu.get_option_by_name('incl_sources').get_value()
        self.incl_notes   = menu.get_option_by_name('incl_notes').get_value()


    def write_report(self):
        """
        Build the actual report.
        """
        
        person1 = self.database.get_person_from_gramps_id(self.person_id)
        self.__generate_qr_code(person1)
        #person2 = self.database.get_person_from_gramps_id(self.person2_id)
        #self.__process_relationship(person1, person2)
       
    def __generate_qr_code(self, person):
        name_string = 'name:'+ person.get_primary_name().get_regular_name() +', grampsid:'+ person.get_gramps_id()
        print(name_string)        
        qr = qrcode.QRCode()
        qr.add_data(name_string)
        qr.make(fit=True)
        img = qr.make_image()
        img.save('temp.png')
        
        self.doc.start_paragraph('QRCG-Normal')
        self.doc.write_text(person.get_primary_name().get_regular_name())
        self.doc.add_media_object('temp.png','left', 3, 3)
        self.doc.end_paragraph()
        
        

    def __process_relationship(self, person1, person2):
        # --- Now let the party begin! ---

        self.doc.start_paragraph('QRCG-Normal')
        #self.doc.
        self.doc.start_paragraph('FSR-Key')
        self.doc.write_text('starting')
        self.doc.end_paragraph()

        self.doc.start_table(None, 'FSR-Table')

        # Main person
        self.doc.start_row()
        self.doc.start_cell('FSR-HeadCell', 3)
        
        self.doc.start_paragraph('FSR-Name')
        self.doc.write_text("First Person\n")
        self.doc.write_text(person1.get_primary_name().get_regular_name())
        event_list = person1.get_event_ref_list()
        for person_event_ref in event_list:
          for e_handle in person_event_ref.get_referenced_handles():
                class_type, handle = e_handle
                if class_type == 'Event':
                    current_event = self.database.get_event_from_handle(handle) #get the revent found in eventref 
                    print('current_event.get_type().string: ',current_event.get_type().string) #takes the event from the database and gets the associated string (type).
                    print('to_struct',current_event.to_struct())
                    print("\n\n")
                       
        self.doc.end_paragraph()
        #self.__dump_person(person1, False, None)

        self.doc.start_paragraph('FSR-Name')
        self.doc.write_text("\nSecond Person\n")
        self.doc.write_text(person1.get_primary_name().get_regular_name())
        self.doc.end_paragraph()
        #self.__dump_person(person2, False, None)
        
        self.doc.start_paragraph('FSR-Name')
        relationship = get_relationship_calculator()
        relate = "\nSecond person is the first person's " + relationship.get_one_relationship(self.database, person1, person2)
        self.doc.write_text(relate)
        self.doc.end_paragraph()

        self.doc.start_paragraph('FSR-Name')
        self.doc.write_text("\nCommon Ancestor\n")
        self.doc.write_text("The common ancestors for Person 1 and Person 2 are ")
        #firstAncestor = self.database.get_person_from_handle();
        info, msg = relationship.get_relationship_distance_new(
                self.database, person1, person2, all_dist=True, only_birth=False)

        self.doc.write_text(self.__process_ancestor_string(info))
        self.doc.end_paragraph()

        #relationship = get_relationship_calculator()
        
        #self.doc.start_paragraph('FSR-Name')
     
                        
        self.doc.end_cell()
        self.doc.end_row()
        self.doc.end_table()

    def __process_ancestor_string(self, info): 
        if type(info).__name__=='tuple':
            return None
        elif type(info).__name__=='list':
            len(info)
            
            ancestorlist=[]
            for relation in info:
                rank = relation[0]
                person_handle = relation[1]
                if rank == -1:
                    return None
                ancestor = self.database.get_person_from_handle(person_handle)
                name = ancestor.get_primary_name().get_regular_name()
                ancestorlist.append(name)
                
            if len(ancestorlist)>0:  
                return ' and '.join(ancestorlist)
            else:
                return None          
                        
_Name_CALLNAME_DONTUSE = 0
_Name_CALLNAME_REPLACE = 1
_Name_CALLNAME_UNDERLINE_ADD = 2

   


#------------------------------------------------------------------------
#
# MenuReportOptions
#
#------------------------------------------------------------------------
class QRCodeOptions(MenuReportOptions):
    """
    Defines options and provides handling interface.
    """

    RECURSE_NONE = 0
    RECURSE_SIDE = 1
    RECURSE_ALL = 2

    def __init__(self, name, dbase):
        MenuReportOptions.__init__(self, name, dbase)


    def add_menu_options(self, menu):

        ##########################
        category_name = _("Report Options")
        ##########################
        self.__filter = FilterOption(_("Filter"), 0)
        self.__filter.set_help(
               _("Select filter to restrict people that appear on calendar"))
        menu.add_option(category_name, "filter", self.__filter)
        
        pid = PersonOption(_("First Relative"))
        pid2 = PersonOption(_("Second Relative"))
        pid.set_help(_("The first person for the relationship calculation."))
        pid2.set_help(_("The second  person for the relationship calculation."))
        menu.add_option(category_name, "pid", pid)
        menu.add_option(category_name, "pid2", pid2)

        recurse = EnumeratedListOption(_("Print sheets for"), self.RECURSE_NONE)
        recurse.set_items([
            (self.RECURSE_NONE, _("Center person only")),
            (self.RECURSE_SIDE, _("Center person and descendants in side branches")),
            (self.RECURSE_ALL,  _("Center person and all descendants"))])
        menu.add_option(category_name, "recurse", recurse)

        callname = EnumeratedListOption(_("Use call name"), _Name_CALLNAME_DONTUSE)
        callname.set_items([
            (_Name_CALLNAME_DONTUSE, _("Don't use call name")),
            (_Name_CALLNAME_REPLACE, _("Replace first name with call name")),
            (_Name_CALLNAME_UNDERLINE_ADD, _("Underline call name in first name / add call name to first name"))])
        menu.add_option(category_name, "callname", callname)

        placeholder = BooleanOption( _("Print placeholders for missing information"), True)
        menu.add_option(category_name, "placeholder", placeholder)
        
        incl_sources = BooleanOption( _("Include sources"), True)
        menu.add_option(category_name, "incl_sources", incl_sources)

        incl_notes = BooleanOption( _("Include notes"), True)
        menu.add_option(category_name, "incl_notes", incl_notes)
    

    def make_default_style(self, default_style):
        """Make default output style for the QR Code Generator Report."""

        #Paragraph Styles
        font = docgen.FontStyle()
        font.set_type_face(docgen.FONT_SANS_SERIF)
        font.set_size(12)
        font.set_bold(0)
        para = docgen.ParagraphStyle()
        para.set_font(font)
        para.set_description(_('The basic style used for the text display'))
        default_style.add_paragraph_style('QRCG-Normal', para)

        font = docgen.FontStyle()
        font.set_type_face(docgen.FONT_SANS_SERIF)
        font.set_size(12)
        font.set_bold(0)
        para = docgen.ParagraphStyle()
        para.set_font(font)
        para.set_alignment(docgen.PARA_ALIGN_LEFT)
        para.set_description(_('The style used for the page key on the top'))
        default_style.add_paragraph_style('FSR-Key', para)

        font = docgen.FontStyle()
        font.set_type_face(docgen.FONT_SANS_SERIF)
        font.set_size(12)
        font.set_bold(1)
        para = docgen.ParagraphStyle()
        para.set_font(font)
        para.set_description(_("The style used for names"))
        default_style.add_paragraph_style('FSR-Name', para)

        font = docgen.FontStyle()
        font.set_type_face(docgen.FONT_SANS_SERIF)
        font.set_size(12)
        font.set_bold(1)
        para = docgen.ParagraphStyle()
        para.set_font(font)
        para.set_alignment(docgen.PARA_ALIGN_CENTER)
        para.set_description(_("The style used for numbers"))
        default_style.add_paragraph_style('FSR-Number', para)

        font = docgen.FontStyle()
        font.set_type_face(docgen.FONT_SANS_SERIF)
        font.set_size(8)
        font.set_bold(0)
        para = docgen.ParagraphStyle()
        para.set_font(font)
        para.set_description(_(
            'The style used for footnotes (notes and source references)'))
        default_style.add_paragraph_style('FSR-Footnote', para)

        #Table Styles
        cell = docgen.TableCellStyle()
        cell.set_padding(0.1)
        cell.set_top_border(1)
        cell.set_left_border(1)
        cell.set_right_border(1)
        default_style.add_cell_style('FSR-HeadCell', cell)

        cell = docgen.TableCellStyle()
        cell.set_padding(0.1)
        cell.set_left_border(1)
        default_style.add_cell_style('FSR-EmptyCell', cell)

        cell = docgen.TableCellStyle()
        cell.set_padding(0.1)
        cell.set_top_border(1)
        cell.set_left_border(1)
        default_style.add_cell_style('FSR-NumberCell', cell)

        cell = docgen.TableCellStyle()
        cell.set_padding(0.1)
        cell.set_top_border(1)
        cell.set_right_border(1)
        cell.set_left_border(1)
        default_style.add_cell_style('FSR-DataCell', cell)

        cell = docgen.TableCellStyle()
        cell.set_padding(0.1)
        cell.set_top_border(1)
        default_style.add_cell_style('FSR-FootCell', cell)

        table = docgen.TableStyle()
        table.set_width(100)
        table.set_columns(3)
        table.set_column_width(0, 7)
        table.set_column_width(1, 7)
        table.set_column_width(2, 86)
        default_style.add_table_style('FSR-Table', table)
