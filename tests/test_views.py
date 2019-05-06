from unittest import mock

from flask import Flask


class TestViews:

    @mock.patch('quaerere_base_flask.views.inspect')
    @mock.patch('quaerere_base_flask.views.importlib')
    def test_view_classes(self, mock_importlib, mock_inspect):
        from quaerere_base_flask.views import _view_classes
        from quaerere_base_flask.views.base import BaseView

        class MockView(BaseView):
            def __init__(self):
                super().__init__(None, mock.MagicMock(), mock.MagicMock())

        module = 'foo'
        mock_inspect.getmembers.return_value = [
            ('MockView', MockView),
            ('MagicMock', mock.MagicMock), ]
        with mock.patch('quaerere_base_flask.views.sys'):
            classes = [I for I in _view_classes(module)]
        mock_importlib.import_module.assert_called_once_with(module)
        assert classes == [MockView]

    @mock.patch('quaerere_base_flask.views._view_classes')
    def test_register_views_defaults(self, mock_view_classes):
        from quaerere_base_flask.views import register_views
        app = mock.MagicMock(Flask)
        view_module = 'view_module'
        version = 'v1'
        view_classes = [mock.MagicMock()]
        route_prefix = f'api/{version}'
        mock_view_classes.return_value = view_classes
        register_views(app, view_module, version)
        view_classes[0].register.assert_called_once_with(
            app,
            route_prefix=route_prefix)

    @mock.patch('quaerere_base_flask.views._view_classes')
    def test_register_views_prefix(self, mock_view_classes):
        from quaerere_base_flask.views import register_views
        app = mock.MagicMock(Flask)
        view_module = 'view_module'
        version = 'v1'
        prefix = 'foo'
        view_classes = [mock.MagicMock()]
        route_prefix = f'{prefix}/{version}'
        mock_view_classes.return_value = view_classes
        register_views(app, view_module, version, prefix)
        view_classes[0].register.assert_called_once_with(
            app,
            route_prefix=route_prefix)

    @mock.patch('quaerere_base_flask.views._view_classes')
    def test_register_views_none(self, mock_view_classes):
        from quaerere_base_flask.views import register_views
        app = mock.MagicMock(Flask)
        view_module = 'view_module'
        version = 'v1'
        view_classes = [mock.MagicMock()]
        mock_view_classes.return_value = view_classes
        register_views(app, view_module, version, prefix=None)
        view_classes[0].register.assert_called_once_with(
            app,
            route_prefix=version)
