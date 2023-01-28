import datetime
import random
import uuid
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from flask_login import current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

from apps.app import db
from apps.crud.models import User
from apps.detector.forms import (
    DeleteForm,
    RegistrateForm,
    SearchBookForm,
    SearchLibraryForm,
    StocktakeForm,
)
from apps.detector.models import RecommendedBook, UserBook, UserLibrary

dt = Blueprint("detector", __name__, template_folder="templates")


@dt.route("/", methods=["GET", "POST"])
@login_required
def index():
    form = SearchBookForm()
    if form.validate_on_submit():
        session["intitle"] = form.title.data
        session["inauthor"] = form.authors.data
        return redirect(url_for("detector.select_book"))

    user_books = (
        db.session.query(User, UserBook)
        .join(UserBook)
        .filter(User.id == UserBook.user_id)
        .all()
    )
    delete_form = DeleteForm()
    stocktake_form = StocktakeForm()

    if "stocks" in session and session["stocks"]:
        stocks = session["stocks"]
    else:
        stocks = ""

    return render_template(
        "detector/index.html",
        user_books=user_books,
        form=form,
        delete_form=delete_form,
        stocktake_form=stocktake_form,
        stocks=stocks,
    )


# 本検索
@dt.route("/search_book", methods=["GET", "POST"])
@login_required
def search_book():
    form = SearchBookForm()
    if form.validate_on_submit():
        session["intitle"] = form.title.data
        session["inauthor"] = form.authors.data
        return redirect(url_for("detector.select_book"))

    return render_template(
        "detector/search_book.html",
        form=form,
    )


# タイトルと著者から検索結果の一覧を表示→ISBNを特定して選択
@dt.route("/select_book")
@login_required
def select_book():
    # ISBN検索
    intitle = session["intitle"]
    inauthor = session["inauthor"]
    url = "https://www.googleapis.com/books/v1/volumes?q="
    url = url + "intitle:" + intitle + "&" + "inauthor:" + inauthor
    r = requests.get(url).json()
    items = r["items"]
    books = []
    i = 0
    for item in items:
        book = {}
        book = {"book_id": str(i)}
        book["title"] = item.get("volumeInfo", {}).get("title", "")
        # 複数著者の場合に配列を文字列に変換
        authors = ""
        for author in item.get("volumeInfo", {}).get("authors", ""):
            authors = authors + " " + author
        book["authors"] = authors
        if item.get("volumeInfo", {}).get("industryIdentifiers") == None:
            book["isbn"] = ""
        # ISBN10のみ抽出
        elif (
            item.get("volumeInfo", {}).get("industryIdentifiers")[0].get("type")
            == "ISBN_10"
        ):
            book["isbn"] = str(
                item.get("volumeInfo", {})
                .get("industryIdentifiers", {})[0]
                .get("identifier", "")
            )
        else:
            book["isbn"] = ""
        books.append(book)
        i = i + 1
        if i > 10:
            break
    session["books"] = books

    registrate_form = RegistrateForm()

    return render_template(
        "detector/select_book.html",
        registrate_form=registrate_form,
    )


# 本をデータベースに登録
@dt.route("/registrate_book/<string:book_id>", methods=["POST"])
@login_required
def registrate_book(book_id):
    try:
        if "books" in session and session["books"]:
            books = session["books"]
        else:
            books = ""
        for book in books:
            if book["book_id"] == book_id:
                title = book["title"]
                authors = book["authors"]
                isbn = book["isbn"]
                user_book = UserBook(
                    user_id=current_user.id, title=title, authors=authors, isbn=isbn
                )

                # ISBNが一致しなければ登録
                if bool(
                    isbn != ""
                    and db.session.query(UserBook).filter(UserBook.isbn == isbn).first()
                ):
                    pass
                else:
                    db.session.add(user_book)
                    db.session.commit()

                break
    except SQLAlchemyError as e:
        flash("本登録処理でエラーが発生しました。")
        current_app.logger.error(e)
        db.session.rollback()

    return redirect(url_for("detector.index"))


# おすすめの本を表示
@dt.route("/recommend_book/<string:media_id>", methods=["GET"])
@login_required
def recommend_book(media_id):
    delete_form = DeleteForm()
    registrate_form = RegistrateForm()
    scrape(media_id)
    recommended_books = (
        db.session.query(RecommendedBook).order_by(RecommendedBook.id.desc()).all()
    )
    return render_template(
        "detector/recommend_book.html",
        delete_form=delete_form,
        registrate_form=registrate_form,
        recommended_books=recommended_books,
        media_id=media_id,
    )


def scrape(media_id):
    # 日経新聞書評
    if media_id == "日経新聞書評":
        # データベースの最終更新日
        query = db.session.query(RecommendedBook)
        if db.session.query(~query.exists()).scalar():
            last_updated_at = datetime.datetime(1900, 1, 1)
        else:
            last_updated_at = (
                query.order_by(RecommendedBook.updated_at.desc()).first().updated_at
            )

        # 最終更新日から1日経過した場合にデータベース更新
        if datetime.datetime.now() > last_updated_at + datetime.timedelta(days=1):
            url = "https://www.nikkei.com/theme/?dw=21110901"
            r = requests.get(url)
            soup = BeautifulSoup(r.text, "html.parser")
            articles = soup.find_all("h3", attrs={"class": "m-miM09_title"})

            books = []
            for article in articles:
                r = requests.get(
                    "https://www.nikkei.com" + article.find("a").get("href")
                )
                soup = BeautifulSoup(r.text, "html.parser")
                articles2 = soup.find_all("div", attrs={"class": "c-post c-flex__col"})
                for article2 in articles2:
                    book = {}
                    book = {
                        "title": article2.find(
                            "h4", attrs={"class": "c-post__title"}
                        ).text
                    }
                    book["authors"] = article2.find(
                        "p", attrs={"class": "c-post__caption"}
                    ).text
                    book["link"] = article2.find("a").get("href")
                    query = db.session.query(RecommendedBook).filter(
                        RecommendedBook.title == book["title"],
                        RecommendedBook.authors == book["authors"],
                        RecommendedBook.media_id == media_id,
                    )
                    if db.session.query(query.exists()).scalar():
                        # データベースに存在する場合も更新
                        book_tmp = query.first()
                        book_tmp.created_at = datetime.datetime.now()
                        db.session.add(book_tmp)
                        db.session.commit()

                        break
                    books.append(book)
                else:
                    continue
                break

            for book in reversed(books):
                recommended_book = RecommendedBook(
                    media_id=media_id,
                    title=book["title"],
                    authors=book["authors"],
                    link=book["link"],
                )
                db.session.add(recommended_book)
            db.session.commit()

    return []


# 蔵書検索
@dt.route("/stocktake/<string:book_id>", methods=["POST"])
@login_required
def stocktake(book_id):
    # appkeyの読み込み
    appkey = current_app.config["CALIL_APP_KEY"]

    user_book = db.session.query(UserBook).filter(UserBook.id == book_id).first()
    user_libraries = (
        db.session.query(UserLibrary)
        .filter(UserLibrary.user_id == current_user.id)
        .all()
    )
    if user_book is None:
        flash("対象の本が存在しません。")
        return redirect(url_for("detector.index"))

    try:
        # ISBN検索
        intitle = user_book.title
        url = "https://www.googleapis.com/books/v1/volumes?q="
        url = url + "intitle:" + intitle
        r = requests.get(url).json()
        ISBN = r["items"][0]["volumeInfo"]["industryIdentifiers"][0]["identifier"]

        # ISBNから蔵書検索
        url = "https://api.calil.jp/check"
        rs = []
        for user_library in user_libraries:
            params = {
                "appkey": appkey,
                "isbn": ISBN,
                "systemid": user_library.systemid,
                "format": "json",
                "callback": "no",
            }
            r = requests.get(url, params).json()
            while r["continue"] == 1:
                params = {
                    "appkey": appkey,
                    "session": r["session"],
                    "format": "json",
                    "callback": "no",
                }
                r = requests.get(url, params).json()
            rs.append(r)

        # 在庫有の図書館情報
        stocks = []
        for r in rs:
            stock = {}
            for systemid in r["books"][str(ISBN)]:
                stock[systemid] = {}
                stock[systemid] = {"book_id": int(book_id)}
                stock[systemid]["status"] = r["books"][str(ISBN)][systemid]["status"]
                stock[systemid]["libkey"] = r["books"][str(ISBN)][systemid]["libkey"]
                # stocktake[k]["formal"] = r["books"][str(ISBN)][k]["formal"]
                stock[systemid]["reserveurl"] = r["books"][str(ISBN)][systemid][
                    "reserveurl"
                ]
            stocks.append(stock)
        session["stocks"] = stocks

    except SQLAlchemyError as e:
        flash("本の検索処理でエラーが発生しました。")
        db.session.rollback()
        current_app.logger.error(e)
        return redirect(url_for("detector.index"))

    return redirect(url_for("detector.index"))


# 本をデータベースから削除
@dt.route("/books/delete/<string:book_id>", methods=["POST"])
@login_required
def delete_book(book_id):
    try:
        db.session.query(UserBook).filter(UserBook.id == book_id).delete()
        db.session.commit()
    except SQLAlchemyError as e:
        flash("本削除処理でエラーが発生しました。")
        current_app.logger.error(e)
        db.session.rollback()

    return redirect(url_for("detector.index"))


# 選択したおすすめの本の候補を取得
@dt.route("/registrate_recommended_book/<string:book_id>", methods=["POST"])
@login_required
def registrate_recommended_book(book_id):
    recommended_book = (
        db.session.query(RecommendedBook).filter(RecommendedBook.id == book_id).first()
    )
    session["intitle"] = recommended_book.title
    session["inauthor"] = recommended_book.authors
    return redirect(url_for("detector.select_book"))


@dt.route("/delete_recommended_book/<string:book_id>", methods=["POST"])
@login_required
def delete_recommended_book(book_id):
    try:
        # db.session.query(RecommendedBook).filter(RecommendedBook.id == book_id).delete()
        db.session.query(RecommendedBook).delete()
        # db.session.delete(RecommendedBook)
        db.session.commit()
    except SQLAlchemyError as e:
        flash("本削除処理でエラーが発生しました。")
        current_app.logger.error(e)
        db.session.rollback()

    # return redirect(url_for("detector.recommend_book"))
    return redirect(url_for("detector.index"))


# 図書館検索
@dt.route("/search_library", methods=["GET", "POST"])
@login_required
def search_library():
    # appkeyの読み込み
    appkey = current_app.config["CALIL_APP_KEY"]

    form = SearchLibraryForm()
    if form.validate_on_submit():
        pref = form.pref.data
        city = form.city.data

        # 図書館検索
        url = "https://api.calil.jp/library"
        params = {
            "appkey": appkey,
            "pref": pref,
            "city": city,
            "format": "json",
            "callback": "no",
        }
        r = requests.get(url, params).json()
        session["libraries"] = r
        return redirect(url_for("detector.select_library"))

    user_libraries = (
        db.session.query(User, UserLibrary)
        .join(UserLibrary)
        .filter(User.id == UserLibrary.user_id)
        .all()
    )
    delete_form = DeleteForm()
    return render_template(
        "detector/search_library.html",
        form=form,
        user_libraries=user_libraries,
        delete_form=delete_form,
    )


# 図書館検索結果を表示
@dt.route("/select_library")
@login_required
def select_library():
    registrate_form = RegistrateForm()

    return render_template(
        "detector/select_library.html",
        registrate_form=registrate_form,
    )


# 図書館をデータベースに登録する
@dt.route("/registrate_library/<string:systemid>", methods=["POST"])
@login_required
def registrate_library(systemid):
    try:
        if "libraries" in session and session["libraries"]:
            libraries = session["libraries"]
        else:
            libraries = ""

        for library in libraries:
            if library["systemid"] == systemid:
                systemid = library["systemid"]
                systemname = library["systemname"]
                libkey = library["libkey"]
                libid = library["libid"]
                short = library["short"]
                formal = library["formal"]

                user_library = UserLibrary(
                    user_id=current_user.id,
                    systemid=systemid,
                    systemname=systemname,
                    libkey=libkey,
                    libid=libid,
                    short=short,
                    formal=formal,
                )
                if bool(
                    db.session.query(UserLibrary)
                    .filter(UserLibrary.systemid == systemid)
                    .first()
                ):
                    pass
                else:
                    db.session.add(user_library)
                    db.session.commit()
                break
    except SQLAlchemyError as e:
        flash("図書館登録処理でエラーが発生しました。")
        current_app.logger.error(e)
        db.session.rollback()

    return redirect(url_for("detector.search_library"))


# 図書館をデータベースから削除する
@dt.route("/libraries/delete/<string:library_id>", methods=["POST"])
@login_required
def delete_library(library_id):
    try:
        db.session.query(UserLibrary).filter(UserLibrary.id == library_id).delete()
        db.session.commit()
    except SQLAlchemyError as e:
        flash("図書館削除処理でエラーが発生しました。")
        current_app.logger.error(e)
        db.session.rollback()

    return redirect(url_for("detector.search_library"))


@dt.errorhandler(404)
def page_not_found(e):
    return render_template("detector/404.html"), 404


# ?????????????????????????????????
# def internal_server_error(e):
#     return render_template("detector/500.html"), 500
