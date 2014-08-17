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
from gramps.gen.display.name import displayer
from gramps.gen.lib import Date, Event, EventType, FamilyRelType, Name
from gramps.gen.lib import StyledText, StyledTextTag, StyledTextTagType
from gramps.gen.plug import docgen
from gramps.gen.plug.menu import BooleanOption, EnumeratedListOption, PersonOption, PersonListOption
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
        filter_option = menu.get_option_by_name('filter')
        self._filter = filter_option.get_filter()
        
    def write_report(self):
        """
        Build the actual report.
        """
        people = self._filter.apply(self.database, self.database.iter_person_handles())
        for indiv in people:
            person = self.database.get_person_from_handle(indiv)
            self.__generate_qr_code(person)
               
    def __generate_qr_code(self, person):
        name_string = 'name:'+ person.get_primary_name().get_regular_name() +', grampsid:'+ person.get_gramps_id()
        
        qr = qrcode.QRCode()
        qr.add_data(name_string)
        qr.make(fit=True)
        img = qr.make_image()
        img.save('temp.png')
        
        self.doc.start_paragraph('QRCG-Normal')
        self.doc.write_text(person.get_primary_name().get_regular_name())
        self.doc.end_paragraph()
   
        self.doc.start_paragraph('QRCG-Normal')
        self.doc.add_media_object('temp.png','center', 3, 3)
        self.doc.end_paragraph()

        self.doc.start_paragraph('QRCG-Normal')
        self.doc.write_text("\n\n\n\n\n\n\n")
        self.doc.end_paragraph()        
        

#------------------------------------------------------------------------
#
# MenuReportOptions
#
#------------------------------------------------------------------------
class QRCodeOptions(MenuReportOptions):
    """
    Defines options and provides handling interface.
    """

    def __init__(self, name, dbase):
        self.__pid = None
        self.__filter = None
        self.__db = dbase
        
        MenuReportOptions.__init__(self, name, dbase)


    def add_menu_options(self, menu):

        ##########################
        category_name = _("Report Options")
        ##########################
        self.__filter = FilterOption(_("Filter"), 0)
        self.__filter.set_help(
               _("A filter used to determine which people are included in the QRCode Generation Report"))
        menu.add_option(category_name, "filter", self.__filter)
        self.__filter.connect('value-changed',self.__filter_changed)
        
        self.__pid = PersonOption(_("Filter Person"))
        self.__pid.set_help(_("This field unlocks when a filter is selected that depends upon this value."))
        menu.add_option(category_name, "pid", self.__pid)
        self.__pid.connect('value-changed', self.__update_filters)
        self.__update_filters()
   
    def __filter_changed(self):
        filter_value = self.__filter.get_value()
        if filter_value in [1, 2, 3, 4]:
            self.__pid.set_available(True)
        else:
            self.__pid.set_available(False)
           
    def __update_filters(self):
        gid = self.__pid.get_value()
        person = self.__db.get_person_from_gramps_id(gid)
        filter_list = utils.get_person_filters(person, False)
        self.__filter.set_filters(filter_list)

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
        para.set_padding(3)
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

        #Graphic Styles
        """
        graphic = docgen.GraphicsStyle()
        graphic.set_paragraph_style(default_style.get_paragraph_style('QRCG-Normal'))
        default_style.add_draw_style('QRCG-Graphic', graphic)
        """
        
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
