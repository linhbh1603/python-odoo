# -*- coding: utf-8 -*-
from odoo import http

# class CookBook(http.Controller):
#     @http.route('/cook_book/cook_book/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cook_book/cook_book/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('cook_book.listing', {
#             'root': '/cook_book/cook_book',
#             'objects': http.request.env['cook_book.cook_book'].search([]),
#         })

#     @http.route('/cook_book/cook_book/objects/<model("cook_book.cook_book"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cook_book.object', {
#             'object': obj
#         })