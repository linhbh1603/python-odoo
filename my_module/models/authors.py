# -*- coding: utf-8 -*-
from   odoo import models, fields, api

class Authors (models.Model):

    _name = 'authors'

    name = fields.Char(string="Authors", required=True)
    old_authors = fields.Integer(string="Old", required=True)
    book_ids = fields.Many2many(
        'library.book',
        string='Books by author'
    )
    count_books = fields.Integer(
        'Number of Authored Books',
        compute='_compute_count_books'
    )

    @api.depends('book_ids')
    def _compute_count_books(self):
        for r in self:
            r.count_books = len(r.book_ids)


