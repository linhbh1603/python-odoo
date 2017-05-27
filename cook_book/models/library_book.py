# -*- coding: utf-8 -*-
import os
from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.fields import Date as fDate
from odoo.exceptions import UserError


class BaseArchive(models.AbstractModel):
    _name = 'base.archive'
    active = fields.Boolean(default=True)

    def do_archive(self):
        for record in self:
            record.active = not record.active


class LibraryBook(models.Model):
    _name = 'library.book'
    _inherit = 'base.archive'
    _description = 'Library Book'
    _order = 'date_release desc, name'
    _rec_name = 'short_name'
    _sql_constraints = [
        ('name_uniq',
         'UNIQUE (name)',
         'Book title must be unique.')
    ]

    name = fields.Char('Title', required=True)
    short_name = fields.Char('Short Title')
    date_release = fields.Date('Release Date')
    isbn = fields.Char('ISBN')
    author_ids = fields.Many2many('res.partner', string='Authors')
    short_name = fields.Char(
        string='Short Title',
        size=100,  # For Char only
        translate=False,  # also for Text fields
    )

    notes = fields.Text('Internal Notes')
    state = fields.Selection(
        [('draft', 'Not Available'),
         ('avaiable', 'Available'),
         ('lost', 'Lost')],
        'State')
    description = fields.Html(
        'Description',
        # optional:
        sanitize=True,
        strip_style=False,
    )
    cover = fields.Binary('Book Cover')
    out_of_print = fields.Boolean('Out of Print?')
    date_release = fields.Date('Release Date')
    date_updated = fields.Datetime('Last Updated')
    reader_rating = fields.Float(
        'Reader Average Rating',
        (14, 4),  # Optional precision (total, decimals)
    )
    pages = fields.Integer(
        string='Number of Pages',
        default=0,
        help='Total book page count',
        groups='base.group_user',
        states={'cancel': [('readonly', True)]},
        copy=True,
        index=False,
        readonly=False,
        required=False,
        company_dependent=False,
    )
    cost_price = fields.Float(
        'Book Cost',
        dp.get_precision('Book Price')
    )
    currency_id = fields.Many2one(
        'res.currency', string='Currency')
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
        related='publisher_id.city'
    )
    author_ids = fields.Many2many(
        'res.partner', string='Authors')
    age_days = fields.Float(
        string='Days Since Release',
        compute='_compute_age',
        inverse='_inverse_age',
        search='_search_age',
        store=False,
        compute_sudo=False,
    )

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (record.id,
                 u"%s (%s)" % (record.name, record.date_release)
                 ))
        return result

    @api.constrains('date_release')
    def _check_release_date(self):
        for r in self:
            if r.date_release > fields.Date.today():
                raise models.ValidationError('Release date must be in the past')

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
    def _referencable_models(self):
        models = self.env['res.request.link'].search([])
        return [(x.object, x.name) for x in models]

    ref_doc_id = fields.Reference(
        selection=_referencable_models,
        string='Reference Document'
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

    @api.model
    def get_all_library_members(self):
        library_member_model = self.env['library.member']
        return library_member_model.search([])

    # Extending write() and create()
    manager_remarks = fields.Text('Manager Remarks')

    @api.model
    @api.returns(lambda rec: rec.id)
    def create(self, values):
        if not self.user_has_groups('library.group_library_manager'):
            if 'manager_remarks' in values:
                raise UserError('You are not allowed to modify manager_remarks')
        return super(LibraryBook, self).create(values)

    @api.multi
    def write(self, values):
        if not self.user_has_groups('library.group_library_manager'):
            if 'manager_remarks' in values:
                raise UserError('You are not allowed to modify manager_remarks')
        return super(LibraryBook, self).write(values)

    # @api.model
    # def fields_get(self,
    #                allfields=None,
    #                write_access=True,
    #                attributes=None):
    #     fields = super(LibraryBook, self).fields_get(
    #         allfields=allfields,
    #         write_access=write_access,
    #         attributes=attributes
    #     )
    #     if not self.user_has_groups('library.group_library_manager'):
    #         if 'manager_remarks' in fields:
    #             fields['manager_remarks']['readonly'] = True


    # Customizing how records are searched
    @api.model
    def name_get(self):
        result = []
        for book in self:
            authors = book.author_ids.mapped('name')
            name = u'%s (%s)' % (book.title, u', '.join(authors))
            result.append((book.id, name))
        return result

    @api.model
    def _name_search(self, name='', args=None, operator='ilike',
                     limit=100, name_get_uid=None):
        args = [] if args is None else args.copy()
        if not (name == '' and operator == 'ilike'):
            args += ['|', '|',
                     ('name', operator, name),
                     ('isbn', operator, name),
                     ('author_ids.name', operator, name)
                     ]
        return super(LibraryBook, self)._name_search(
            name='', args=args, operator='ilike',
            limit=limit, name_get_uid=name_get_uid)


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _order = 'name'

    book_ids = fields.One2many(
        'library.book', 'publisher_id',
        string='Published Books')

    book_ids = fields.Many2many(
        'library.book',
        string='Authored Books',
        # relation='library_book_res_partner_rel'  # optional
    )
    authored_book_ids = fields.Many2many(
        'library.book', string='Authored Books')
    count_books = fields.Integer(
        'Number of Authored Books',
        compute='_compute_count_books'
    )

    @api.depends('authored_book_ids')
    def _compute_count_books(self):
        for r in self:
            r.count_books = len(r.authored_book_ids)


class LibraryMember(models.Model):
    _name = 'library.member'
    _inherits = {'res.partner': 'partner_id'}

    partner_id = fields.Many2one(
        'res.partner',
        ondelete='cascade')

    date_start = fields.Date('Member Since')
    date_end = fields.Date('Termination Date')
    member_number = fields.Char()


class SomeModel(models.Model):
    _name = 'some.model'

    data = fields.Text('Data')

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

    @api.multi
    def create_company(self):
        today_str = fields.Date.contex_today()
        val1 = {'name': u'Eric Idel',
                'email': u'eric.idle@example.com',
                'date': today_str,
                }
        val2 = {'name': u'John Cleese',
                'email': u'john.cleese@example.com',
                'date': today_str,
                }
        company_val = {'name': u'Flying Circus',
                       'email': u'm.python@example.com',
                       'date': today_str,
                       'is_company': True,
                       'child_ids': [(0, 0, val1),
                                     (0, 0, val2),
                                     ],
                       }
        record = self.env['res.company'].create(company_val)
        return record

    @api.model
    def add_contact(self, partner, contacts):
        partner.ensure_one()
        if contacts:
            partner.date = fields.Date.context_today()
            partner.child_ids |= contacts

    @api.model
    def add_contacts_option2(self, partner, contacts):
        partner.ensure_one()
        if contacts:
            today = fields.Date.context_today()
            partner.update(
                {'date': fields.Date.to_string(today),
                 'child_ids': partner.child_ids | contacts}
            )

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

    # Filtering recordsets
    @api.model
    def partners_with_email(self, partners):
        def predicate(partner):
            if partner.email:
                return True
            return False

        return partners.filter(predicate)

    @api.model
    def partners_with_email_variant(self, partners):
        return partners.filter(lambda p: p.email)

    @api.model
    def partners_with_email_variant2(self, partners):
        return partners.filter('email')

    # Traversing recordset relations
    @api.model
    def get_email_addresses(self, partner):
        # This will make sure we have one record, not multiple records.
        partner.ensure_one()
        return partner.mapped('child_ids.email')

    @api.model
    def get_companies(self, partners):
        return partners.mapped('parent_id')


# Chapter_6_1_Change the user performing an action
class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def update_phone_number(self, new_number):
        self.ensure_one()
        company_as_superuser = self.sudo()
        company_as_superuser.phone = new_number


# chapter_6
class LibraryBookLoan(models.Model):
    _name = 'library.book.loan'
    book_id = fields.Many2one('library.book', 'Book', required=True)
    member_id = fields.Many2one('library.member', 'Borrower',
                                required=True)
    state = fields.Selection([('ongoing', 'Ongoing'),
                              ('done', 'Done')],
                             'State',
                             default='ongoing', require=True)


# chapter_6
class LibraryLoanWizard(models.TransientModel):
    _name = 'library.loan.wizard'
    member_id = fields.Many2one('library.member', 'Member')
    book_ids = fields.Many2many('library.book', 'Books')

    @api.multi
    def record_loans(self):
        for wizard in self:
            member = wizard.member_id
            loan = self.env['library.book.loan']
            for book in wizard.book_ids:
                loan.create({'member_id': member.id,
                             'book_id': book.id})
