"""为学员准备项目数据:基于 Olist 真实电商数据(2万单子集) + 参数化再脏化。

用法: python prepare_data.py [seed]
  seed 不传则随机生成。同一 seed 产出完全相同的数据,方便复现。

产出: ./project_data/ 目录,含 6 张 CSV + 数据说明.md

再脏化规则(叠加在真实数据自带的缺失之上):
  1. order_items.price: ~3% 的值带上 "R$ " 前缀变成字符串(练 str 清洗 + astype)
  2. order_items: 随机复制 ~1% 的行(练 drop_duplicates,且要先想清楚"什么算重复")
  3. products.product_category_name: ~5% 加随机大小写/首尾空格(练 str.strip/lower)
  4. order_items.price: 注入 8 条小数点错位的离谱价格(练异常值识别)
真实数据自带的脏(不是我们造的,面试可以照实讲):
  - orders 表约 3% 的订单缺 order_delivered_customer_date,且与订单状态相关(非随机缺失!)
  - 所有日期列都是字符串,需要 to_datetime
"""
import sys
import random
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

SKILL_DATA = Path(__file__).resolve().parent.parent / "data"
OUT = Path.cwd() / "project_data"

GITHUB_FALLBACK = "https://github.com/spdrio/Brazilian-E-Commerce-Public-Dataset-by-Olist.git"


def load_base():
    if SKILL_DATA.exists():
        return {p.stem: pd.read_csv(p) for p in SKILL_DATA.glob("*.csv")}
    raise FileNotFoundError(
        f"找不到内置数据目录 {SKILL_DATA}。"
        f"可从镜像手动获取后放入该目录: {GITHUB_FALLBACK}"
    )


def dirty(tables: dict, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    items = tables["order_items"].copy()
    products = tables["products"].copy()

    # 1. 价格列混入 "R$ " 前缀 → 整列变 object
    n = len(items)
    idx = rng.choice(n, size=int(n * 0.03), replace=False)
    items["price"] = items["price"].astype(str)
    items.loc[items.index[idx], "price"] = "R$ " + items.loc[items.index[idx], "price"]

    # 4. 小数点错位的离谱价格(在加前缀之前是 float,这里直接改字符串值)
    out_idx = rng.choice(n, size=8, replace=False)
    for i in out_idx:
        v = items.iloc[i]["price"].replace("R$ ", "")
        items.iloc[i, items.columns.get_loc("price")] = str(round(float(v) * 100, 2))

    # 2. 复制 1% 的行作为重复
    dup = items.sample(frac=0.01, random_state=seed)
    items = pd.concat([items, dup], ignore_index=True)
    items = items.sample(frac=1, random_state=seed).reset_index(drop=True)

    # 3. 品类名大小写/空格噪音
    m = len(products)
    noisy = rng.choice(m, size=int(m * 0.05), replace=False)
    col = products.columns.get_loc("product_category_name")
    for i in noisy:
        v = products.iloc[i, col]
        if isinstance(v, str):
            v = v.upper() if rng.random() < 0.5 else " " + v + " "
            products.iloc[i, col] = v

    tables = dict(tables)
    tables["order_items"] = items
    tables["products"] = products
    return tables


README = """# 项目数据说明

你是一家电商平台的数据分析师。运营负责人给了你一句话需求:

> "用户好像对我们的物流不太满意,你帮我看看数据,给点结论和建议。"

数据来自巴西电商平台 Olist 的 10 万订单公开数据集(2016-2018 真实商业数据,
已脱敏),本项目使用其中 2 万单的子集。

| 文件 | 内容 | 关键列 |
|---|---|---|
| orders.csv | 订单主表 | order_id, customer_id, 各环节时间戳, order_status |
| order_items.csv | 订单商品明细(一单可多件) | order_id, product_id, price, freight_value |
| products.csv | 商品信息 | product_id, product_category_name(葡语) |
| reviews.csv | 订单评价 | order_id, review_score(1-5) |
| customers.csv | 客户信息 | customer_id, customer_unique_id, customer_state |
| payments.csv | 支付记录 | order_id, payment_type, payment_value |
| category_translation.csv | 品类葡语→英语对照 | |

注意:customer_id 是"订单级"的(每单一个),customer_unique_id 才是真正的
用户标识。这是真实数据里的一个坑,也是面试官爱问的点。

数据没有经过清洗,带着它真实(以及一点人为追加)的脏。这正是你的起点。
"""


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else random.randint(1000, 9999)
    tables = dirty(load_base(), seed)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for name, df in tables.items():
        if name == "category_translation":
            df.to_csv(OUT / f"{name}.csv", index=False)
        else:
            df.to_csv(OUT / f"{name}.csv", index=False)
    (OUT / "数据说明.md").write_text(README, encoding="utf-8")
    print(f"数据已就绪: {OUT}  (seed={seed},记录该值可复现)")
    for p in sorted(OUT.glob("*.csv")):
        print(f"  {p.name}: {sum(1 for _ in open(p)) - 1} 行")


if __name__ == "__main__":
    main()
