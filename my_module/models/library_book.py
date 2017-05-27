# -*- coding: utf-8 -*-
import os
import time
from odoo import models, fields, api
from odoo.fields import Date as fDate
from datetime import timedelta as td
from odoo.exceptions import UserError
from datetime import date

class BaseArchive(models.AbstractModel):
    _name = 'base.archive'
    active = fields.Boolean(default=True)

    def do_archive(self):
        for record in self:
            record.active = not record.active

class LibraryBook(models.Model):
    _name = 'library.book'
    _inherit = ['base.archive']
    _description = 'Book'
    _order = 'date_release desc, name'
    _rec_name = 'short_name'
    short_name = fields.Char(
        string='Short Title',
        size=100,
        translate=False,
    )
    manager_remarks = fields.Text('Manager Remarks')
    notes = fields.Text('Internal Notes')
    state = fields.Selection(
        [('draft', 'Not Avaiable'),
         ('avaiable', 'Avaiable'),
         ('lost', 'Lost')],
        'State')
    description = fields.Html(
        string='Description',
        # optional:
        sanitize=True,
        strip_style=False,
        translate=False,
    )
    cover = fields.Binary('Book Cover')
    name = fields.Char('Title', required=True)
    date_release = fields.Date('Release Date', required=True)
    date_updated = fields.Datetime('Last Updated')
    pages = fields.Integer(
        string='Number of Pages',
        default=100,
        help='Total book page count',
        # groups     = 'base.group_users',
        # states     = {'cancel': [('readonly', True)]},
        # copy       = True,
        # index      = False,
        # readonly   = False,
        required=True,
        # company_dependent=False,
    )

    reader_rating = fields.Float(
        'Reader Average Rating',
        (14, 4)
    )
    author_ids = fields.Many2many('authors', string='Authors')
    price = fields.Float(string="Price", required=True)
    sale_off = fields.Float(string="Sale off")
    cost_price = fields.Float(compute='_compute_cost_price')
    age_days = fields.Float(
        string='Days Since Release',
        compute='_compute_age',
        inverse='_inverse_age',
        search='_search_age',
        store=False,
        compute_sudo=False,
    )
    state = fields.Selection([('draft', 'Unavailable'),
                              ('available', 'Available'),
                              ('borrowed', 'Borrowed'),
                              ('lost', 'Lost')],
                             'State')

    @api.model
    def is_allowed_transition(self, old_state, new_state):
        allowed = [('draft', 'available'),
                   ('available', 'borrowed'),
                   ('borrowed', 'available'),
                   ('available', 'lost'),
                   ('borrowed', 'lost'),
                   ('lost', 'available')]
        return (old_state, new_state) in allowed

    @api.multi
    def change_state(self, new_state):
        for book in self:
            if book.is_allowed_transition(book.state, new_state):
                book.state = new_state
            else:
                continue

    @api.depends('date_release')
    def _compute_age(self):
        today = fDate.from_string(fDate.today())
        for book in self.filtered('date_release'):
            delta = (fDate.from_string(book.date_release) - today)
            book.age_days = delta.days
    def _inverse_age(self):
        today = fDate.from_string(fDate.today())
        for book in self.filtered('date_release'):
            d = td(days=book.age_days) - today
            book.date_release = fDate.to_string(d)
    def _search_age(self, operator, value):
        today = fDate.from_string(fDate.today())
        value_days = td(days=value)
        value_date = fDate.to_string(today - value_days)
        return [('date_release', operator, value_date)]

    @api.model
    def _compute_cost_price(self):
        return self.env['decimal_precision'].precision_get('Book Price')

    currency_id = fields.Many2one('res.currency', string='Currency')
    retail_price = fields.Monetary(
        'Retail Price',
        # optional: currency_field='currency_id',
    )
    publisher_id = fields.Many2one(
        'res.partner', string='Publisher',
        # optional:
        ondelete='set null',
        context={},
        domain=[],
    )
    publisher_city = fields.Char(
        'Publisher City',
        related='publisher_id.city')

    _sql_constraints = [(
        'name_uniq',
        'UNIQUE (name)',
        'Book title must be unique.'
    )]

    @api.constrains('name')
    def _check_name(self):
        for r in self:
            if 'book' not in r.name:
                raise models.ValidationError('Name phai co tu book o trong')

    @api.constrains('date_release')
    def _check_release_date(self):
        for r in self:
            if r.date_release > fields.Date.today():
                raise models.ValidationError('Release date must be in the past')

    @api.onchange('pages')
    def _check_pages(self):
        if self.pages<50:
            raise models.ValidationError('Pages phai lon hon 50')

    ref_doc_id = fields.Reference(
        selection='_referencable_models',
        string='Reference Document')

    @api.model
    def _referencable_models(self):
        models = self.env['res.request.link'].search([])
        return [(x.object, x.name) for x in models]

    @api.model
    def get_all_library_member(self):
        library_member_model = self.env['library.member']
        return library_member_model.search([])

class ResPartner(models.Model):

    _inherit = 'res.partner'
    _order = "name"
    book_id = fields.One2many(
            'library.book',
            'publisher_id',
            string='Published Books'
    )

    # create new record (chua hoan thanh)
    _name = 'res.partner'
    name = fields.Char('Name', required=True)
    email = fields.Char('Email')
    date = fields.Date('Date')
    is_company = fields.Boolean('Is a company')
    parent_id = fields.Many2one('res.partner', 'Related Company')
    child_ids = fields.One2many('res.partner', 'parent_id', 'Contacts')
    # today_str = date.today().strftime('%Y-%m-%d')

    # @api.multi
    # def create(self):
    #     today_str = fields.Date.today()
    #     val1 = {'name': u'Eric Idle',
    #             'email': u'eric.idle@example.com',
    #             'date': today_str}
    #     val2 = {'name': u'John Cleese',
    #             'email': u'john.cleese@example.com',
    #             'date': today_str}
    #     partner_val = {
    #         'name': u'Flying Circus',
    #         'email': u'm.python@example.com',
    #         'date': today_str,
    #         'is_company': True,
    #         'child_ids': [(0, 0, val1),
    #                       (0, 0, val2),
    #                       ]
    #     }
    #     record = self.env['res.partner'].create(partner_val)

    # #updating values of recordset record
    # @api.model
    # def add_contacts(self, partner, contacts):
    #     partner.ensure_one()
    #     if contacts:
    #         partner.date = fields.Date.context_today()
    #         partner.child_ids |= contacts

    #Search for record
    @api.model
    def find_partners_and_contacts(self, name):
        partner = self.env['res.partner']
        domain = ['|',
                  '&',
                  ('is_company', '=', True),
                  ('name', 'like', name),
                  '&',
                  ('is_company', '=', False),
                  ('parent_id.name', 'like', name)
                  ]
        return partner.search(domain)

    #filtering recordset
    @api.model
    def partners_with_email(self, partners):
        def predicate(partner):
            if partner.email:
                return True
        return False
        return partners.filter(predicate)

    #Traversing recordset relation
    @api.model
    def get_email_addresses(self, partner):
        partner.ensure_one()
        return partner.mapped('child_ids.email')

    @api.model
    def get_companies(self, partners):
        return partners.mapped('parent_id')

    #Extending the business logic defined in a Model


class LibraryMember(models.Model):
    _inherit = 'res.partner'
    _name = 'library.member'

    partner_id = fields.Many2one(
        'res.partner',
        ondelete='cascade')
    date_start = fields.Date('Member Since')
    date_end = fields.Date('Termination Date')
    member_number = fields.Char()

class SomeModel(models.Model):
    data = fields.Text('Data')
    _name = 'some.model'
    @api.multi
    def save(self, filename):
        path = os.path.join('/opt/exports', filename)
        with open(path, 'w') as fobj:
            for record in self:
                fobj.write(record.data)
                fobj.write('\n')

    @api.multi
    def save(self, filename):
        if '/' in filename or '\\' in filename:
            raise UserError('Illegal filename %s' % filename)
        path = os.path.join('/opt/exports', filename)
        try:
            with open(path, 'w') as fobj:
                for record in self:
                    fobj.write(record.data)
                    fobj.write('\n')
        except (IOError, OSError) as exc:
            message = 'Unable to save file: %s' % exc
            raise UserError(message)


