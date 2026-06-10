"""电商物流口碑分析 — 完整流水线(Olist 2万订单子集)
运行: python analysis.py  (需 project_data/ 在同目录)
产出: findings.md + 各结果表
结构: 清洗 → 假设验证(地区/时间/时长/品类) → 稳健性(分层/回归/拆段) → 反事实测算
"""
import pandas as pd, numpy as np

# ---------- 1. 读取与清洗 ----------
orders = pd.read_csv('project_data/orders.csv')
orders['is_delivered'] = orders['order_status'] == 'delivered'          # 结构性缺失→标记而非删行
for c in orders.columns:
    if 'date' in c or 'timestamp' in c or c == 'order_approved_at':
        orders[c] = pd.to_datetime(orders[c])

items = pd.read_csv('project_data/order_items.csv')
items['price'] = items['price'].str.replace('R$ ', '', regex=False).astype(float)  # 货币符号清洗
items = items.drop_duplicates()                                          # 整行重复=数据错误(同单同品有独立行号)
med = items.groupby('product_id')['price'].transform('median')
items = items[items['price'] <= med * 10]                                # 超同商品中位价10倍→录入错误

reviews = (pd.read_csv('project_data/reviews.csv')
             .sort_values('review_creation_date').drop_duplicates('order_id', keep='last'))
prods = pd.read_csv('project_data/products.csv')
prods['cat'] = prods['product_category_name'].astype(str).str.strip().str.lower()  # 分组前统一大小写
cust = pd.read_csv('project_data/customers.csv')
trans = pd.read_csv('project_data/category_translation.csv')

# 每单取金额最高商品的品类
order_cat = (items.merge(prods[['product_id','cat']], on='product_id', how='left')
                  .sort_values('price', ascending=False).drop_duplicates('order_id'))

d = (orders[orders.is_delivered]
     .merge(reviews[['order_id','review_score']], on='order_id', how='left', validate='1:1')
     .merge(order_cat[['order_id','cat']], on='order_id', how='left')
     .merge(cust[['customer_id','customer_state']], on='customer_id', how='left'))
d['配送天数'] = (d.order_delivered_customer_date - d.order_purchase_timestamp).dt.days
d['月份'] = d.order_purchase_timestamp.dt.to_period('M').astype(str)
d['速度档'] = pd.cut(d['配送天数'], [0,7,14,21,999], labels=['≤7天','8-14天','15-21天','>21天'])
d['bad'] = (d.review_score <= 2)

bad_rate = lambda s: (s <= 2).mean() * 100

# ---------- 2. 假设验证 ----------
h_state = d.groupby('customer_state').agg(订单量=('order_id','nunique'),
            差评率=('review_score', bad_rate)).sort_values('订单量', ascending=False).head(8)
h_month = d.groupby('月份').agg(订单量=('order_id','nunique'), 差评率=('review_score', bad_rate),
            配送中位数=('配送天数','median'))
h_speed = d.groupby('速度档', observed=True).agg(订单数=('order_id','size'),
            差评率=('review_score', bad_rate))                            # 核心:剂量反应梯度

# ---------- 3. 稳健性 ----------
top6 = d['cat'].value_counts().head(6).index
h_strat = d[d.cat.isin(top6)].pivot_table(index='cat', columns='速度档',
            values='review_score', aggfunc=bad_rate, observed=True)      # 品类分层:行内单调=稳健
try:
    import statsmodels.formula.api as smf
    dd = d.dropna(subset=['速度档','review_score']).copy()
    dd['st'] = np.where(dd.customer_state.isin(dd.customer_state.value_counts().head(5).index),
                        dd.customer_state, 'OTH')
    dd['c6'] = np.where(dd.cat.isin(top6), dd.cat, 'other')
    m = smf.logit('bad ~ C(速度档) + C(st) + C(c6)', data=dd.assign(bad=dd.bad.astype(int))).fit(disp=0)
    ors = np.exp(m.params).filter(like='速度档').round(2)                 # 控混杂后的几率比
except ImportError:
    ors = '需 pip install statsmodels'
seg = d.dropna(subset=['order_delivered_carrier_date'])
seg = seg.assign(卖家段=(seg.order_delivered_carrier_date-seg.order_purchase_timestamp).dt.days,
                 运输段=(seg.order_delivered_customer_date-seg.order_delivered_carrier_date).dt.days)
h_seg = seg.groupby(seg.bad.map({True:'差评单',False:'好/中评单'}))[['卖家段','运输段']].median()

# ---------- 4. 反事实测算 ----------
slow = d[d.配送天数 > 21]; mid = bad_rate(d[(d.配送天数>14)&(d.配送天数<=21)].review_score)/100
saved = slow.bad.sum() - len(slow)*mid
counterfactual = (d.bad.mean()*100, (d.bad.mean() - saved/len(d))*100)

# ---------- 5. 落盘 ----------
with open('findings.md','w') as f:
    f.write('# 分析结果汇总\n\n## 州×差评率\n'+h_state.round(1).to_markdown())
    f.write('\n\n## 月度趋势\n'+h_month.round(1).to_markdown())
    f.write('\n\n## 核心:速度档×差评率\n'+h_speed.round(1).to_markdown())
    f.write('\n\n## 品类分层稳健性\n'+h_strat.round(1).to_markdown())
    f.write(f'\n\n## logistic回归 OR(控州+品类)\n{ors}\n')
    f.write('\n## 配送拆段(中位天数)\n'+h_seg.to_markdown())
    f.write(f'\n\n## 反事实:长尾压缩后全平台差评率 {counterfactual[0]:.1f}% -> {counterfactual[1]:.1f}%\n')
print('完成,结果见 findings.md')
