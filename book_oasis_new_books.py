# -*- coding: utf-8 -*-
from plugins.metadata.base import BaseMetadataProvider
import urllib.parse


class BookOasisNewBooksProvider(BaseMetadataProvider):
    """
    대시보드 메인 화면에 북오아시스에 새로 등록된 도서 30권의 목록을 제공하는 플러그인입니다.
    """
    id = "book_oasis_new_books"
    name = "북오아시스 신규 등록 도서 30"
    is_searchable = False
    config_schema = []
    dashboard_widget = {
        'title': '북오아시스 최근 등록 도서',
        'subtitle': '최근에 새로 등록된 도서 30권을 대시보드에 표시합니다.',
        'provider': 'BookOasis',
        'icon': 'fa-solid fa-book-bookmark',
        'limit': 30,
        'all_desk_tab': True,
    }
    update_manifest = {
        "enabled": True,
        "provider": "github-raw",
        "raw_base_url": "https://raw.githubusercontent.com/leeyj/BookOasis_stable/main/plugins/metadata/book_oasis_new_books",
        "files": ["book_oasis_new_books.py", "__init__.py", "VERSION"],
        "version_file": "VERSION",
        "version_key": "plugin version",
        "show_sample_update_button": True,
    }

    def search(self, db_type, query):
        return []

    def apply(self, db_type, book_id, item_data):
        return False, "이 플러그인은 대시보드 전용으로 메타데이터 매칭을 지원하지 않습니다."

    def _generate_book_url(self, db_type, row):
        """요청하신 해시 스타일 상세 페이지 주소를 생성합니다."""
        book_id = row.get('id')
        title = row.get('title') or ''
        series_name = row.get('series_name') or ''
        
        try:
            library_id = int(db_type)
        except (TypeError, ValueError):
            library_id = 1

        display_title = series_name if series_name else title
        
        params = {
            'series': display_title,
            'libraryId': library_id,
            'repBookId': book_id,
            'displayTitle': display_title
        }
        
        query_string = urllib.parse.urlencode(params)
        return f"/#detail?{query_string}"

    def _fetch_new_books(self, db_type, limit=30):
        gateway = self.get_db_gateway(db_type)
        try:
            rows = gateway.fetch_all(
                """
                SELECT *
                FROM books
                WHERE COALESCE(is_deleted, 0) = 0
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,)
            )

            results = []
            for row in rows:
                if not isinstance(row, dict):
                    try:
                        row = dict(row)
                    except Exception:
                        row = {}

                book_id = row.get('id')
                title = row.get('title') or '제목 없음'
                author = row.get('author') or '저자 미상'
                publisher = row.get('publisher') or ''
                pub_date = row.get('pub_date') or row.get('pubDate') or ''
                cover = row.get('cover_url') or row.get('cover') or ''
                description = row.get('description') or ''
                created_at = row.get('created_at') or ''

                detail_url = self._generate_book_url(db_type, row)

                results.append({
                    'id': book_id,
                    'title': title,
                    'author': author,
                    'publisher': publisher,
                    'pubDate': pub_date,
                    'cover': cover,
                    'description': description,
                    'createdAt': created_at,
                    'link': detail_url
                })

            return {'success': True, 'books': results}
        except Exception as e:
            import traceback
            print(f"[BookOasisNewBooksProvider] 신규 등록 도서 조회 예외 발생: {e}")
            print(traceback.format_exc())
            return {'success': False, 'error': str(e)}

    def get_dashboard_data(self, db_type, limit=30):
        limit_val = max(1, int(limit or 30))
        result = self._fetch_new_books(db_type, limit=limit_val)
        if not result.get('success'):
            return result
        
        return {
            'success': True,
            'items': result.get('books', [])
        }

    def get_context_menu_items(self, db_type, context):
        return [
            {
                'id': 'open_book_detail',
                'label': '도서 상세 정보 보기',
                'icon': 'fa-solid fa-circle-info',
            }
        ]

    def run_context_menu_action(self, db_type, action_id, context):
        if action_id != 'open_book_detail':
            return {'success': False, 'error': f'지원하지 않는 액션입니다: {action_id}'}

        book_id = (context or {}).get('book_id') or (context or {}).get('id')
        if not book_id:
            return {'success': False, 'error': '도서 ID 정보가 없어 상세 페이지를 열 수 없습니다.'}

        detail_url = self._generate_book_url(db_type, context)

        return {
            'success': True,
            'message': '도서 상세 페이지로 이동합니다.',
            'open_url': detail_url,
        }
