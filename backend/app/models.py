from . import db
from sqlalchemy import UniqueConstraint, func
from sqlalchemy.orm import relationship

class Stock(db.Model):
    __tablename__ = 'stock'
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String, unique=True, nullable=False, index=True)
    name = db.Column(db.String, nullable=True)
    sector = db.Column(db.String, nullable=True)
    industry = db.Column(db.String, nullable=True)
    logo_url = db.Column(db.String, nullable=True)

    price_data = relationship("PriceData", backref="stock")
    fundamental_data = relationship("FundamentalData", backref="stock", uselist=False)
    news_articles = relationship("NewsArticle", backref="stock")

    def __repr__(self):
        return f'<Stock {self.ticker}>'

class PriceData(db.Model):
    __tablename__ = 'price_data'
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    open = db.Column(db.Numeric, nullable=True)
    high = db.Column(db.Numeric, nullable=True)
    low = db.Column(db.Numeric, nullable=True)
    close = db.Column(db.Numeric, nullable=False)
    volume = db.Column(db.BigInteger, nullable=True)

    __table_args__ = (UniqueConstraint('stock_id', 'date', name='uq_stock_date'),)

    def __repr__(self):
        return f'<PriceData {self.stock.ticker} {self.date}>'

class FundamentalData(db.Model):
    __tablename__ = 'fundamental_data'
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False, unique=True)
    market_cap = db.Column(db.Numeric, nullable=True)
    pe_ratio = db.Column(db.Numeric, nullable=True)
    pb_ratio = db.Column(db.Numeric, nullable=True)
    dividend_yield = db.Column(db.Numeric, nullable=True)
    eps = db.Column(db.Numeric, nullable=True)  # Earnings Per Share
    roe = db.Column(db.Numeric, nullable=True)  # Return On Equity
    last_updated = db.Column(db.DateTime, default=func.now())

    def __repr__(self):
        return f'<FundamentalData {self.stock.ticker}>'

class NewsArticle(db.Model):
    __tablename__ = 'news_article'
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=True)
    title = db.Column(db.String, nullable=False)
    url = db.Column(db.String, nullable=False, unique=True)
    source_name = db.Column(db.String, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String, nullable=True)
    published_at = db.Column(db.DateTime, nullable=False, index=True)
    fetched_at = db.Column(db.DateTime, default=func.now())

    def __repr__(self):
        return f'<NewsArticle {self.title[:50]}>'
