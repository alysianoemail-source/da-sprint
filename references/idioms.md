# 25 个句型:一个数分项目的全部 pandas

记业务动作,不记函数名。括号内为出现频率权重:★★★ 必须练到白纸级,★★ 练到改写级,★ 见过会查即可。

## 一、读取与初识

1. **打开数据先看三眼** (★★★)
   `pd.read_csv(path)` → `df.head()` / `df.info()` / `df.shape`
   info 看三件事:行数、每列类型、每列非空数。

2. **这列都有什么值** (★★★)
   `df['col'].value_counts()` —— 加 `normalize=True` 看占比,加 `dropna=False` 把缺失也数进来。

3. **数值列的体检报告** (★★)
   `df['col'].describe()` —— 先看 min/max 是否离谱,再看均值和中位数差多远。

## 二、清洗

4. **缺失盘点** (★★★)
   `df.isna().sum()` —— 永远先盘点再处置。追问:缺失是随机的吗?按某个维度 groupby 一下缺失率。

5. **缺失处置三选一** (★★★)
   `df.dropna(subset=[...])` / `df['col'].fillna(值)` / 保留缺失新建标记列。
   选哪个取决于缺失机制,不是个人喜好。

6. **去重** (★★)
   `df.duplicated().sum()` → `df.drop_duplicates()`
   先回答:什么算"重复"?整行相同,还是某个 id 相同?`subset=` 参数由答案决定。

7. **类型修正** (★★★)
   `df['col'].astype(float)` / `pd.to_datetime(df['col'])`
   带杂质的字符串先 `df['col'].str.replace('R$ ', '', regex=False)` 再转。

8. **字符串整容** (★★)
   `df['col'].str.strip().str.lower()` —— 分组前不做这步,同一类会被算成好几类。

9. **异常值识别与处置** (★★)
   `df['col'].quantile([0.01, 0.99])` + 布尔过滤。处置写明理由:删、截断(clip)、还是保留单独说明。

## 三、变换

10. **按条件取子集** (★★★)
    `df[df['col'] > x]`、多条件 `df[(a) & (b)]` 各自带括号。这是所有分析的地基。

11. **造新列** (★★★)
    `df['new'] = 表达式` —— 例如 `df['配送天数'] = (df['delivered'] - df['purchase']).dt.days`

12. **值映射** (★★)
    `df['col'].map({'a': '甲', 'b': '乙'})` —— 翻译、归类、打标都是它。

13. **时间维度拆解** (★★★)
    `df['dt'].dt.month` / `.dt.dayofweek` / `.dt.date` —— 趋势分析的前置动作。

14. **连续值分箱** (★★)
    `pd.cut(df['col'], bins=[...], labels=[...])` 自定边界 / `pd.qcut(df['col'], 4)` 等频。
    价格带、时长档、RFM 分层全是它。

15. **排序与 TopN** (★★★)
    `df.sort_values('col', ascending=False).head(10)` 或 `df.nlargest(10, 'col')`

## 四、聚合(项目的发动机)

16. **分组聚合** (★★★,本表之王)
    `df.groupby('维度')['度量'].mean()`
    多指标: `df.groupby('维度').agg(均价=('price','mean'), 单量=('order_id','nunique'))`

17. **多维交叉** (★★)
    `df.pivot_table(index='维度1', columns='维度2', values='度量', aggfunc='mean')`

18. **多表关联** (★★★)
    `df1.merge(df2, on='key', how='left')`
    merge 完必查行数:变多 = 右表 key 不唯一(一对多),想清楚这是否符合预期。

19. **组内占比/排名** (★★)
    `df['组内占比'] = df['x'] / df.groupby('维度')['x'].transform('sum')`

20. **聚合到分析单位** (★★★)
    订单级 → 用户级: `df.groupby('customer_unique_id').agg(总单数=..., 总金额=..., 末单时间=...)`
    一行代表什么,由这一步决定。

## 五、输出

21. **快速画图** (★★)
    `df.plot(kind='bar')` / `kind='line'` —— 一个结论一张图,图标题写结论而不是变量名。

22. **比例的正确算法** (★★★)
    差评率 = `(s <= 2).mean()` —— 布尔均值即比例,面试笔试高频。

23. **数字的最后一公里** (★★)
    `.round(2)`、`.rename(columns=...)`、`.reset_index()` —— 给人看的表才算产出。

24. **落盘** (★)
    `df.to_csv('out.csv', index=False)`

25. **链式思维** (★)
    `df[筛选].groupby(维度)[度量].mean().sort_values()` —— 把前面的句型连成一句话,
    读出声:"筛出已送达的,按品类分组,算平均配送天数,从慢到快排"。能读出声就能写出来。

---
超纲问题统一回复:"面试用不上,遇到现查。"包括但不限于:apply 的花式用法、
多级索引、stack/unstack、性能优化。

---
## 附录:Stata → pandas 对照(有 Stata 底子的学员用)

| Stata | pandas |
|---|---|
| merge 1:1 id using b | a.merge(b, on='id', validate='1:1') |
| merge m:1 / 1:m | validate='m:1' / '1:m' |
| _merge 变量 | merge(..., indicator=True) 生成 _merge 列 |
| keep if _merge==3 | how='inner'(注意:pandas merge **默认即 inner,会悄悄丢行**) |
| append using b | pd.concat([a, b]) |
| collapse (mean) x, by(g) | df.groupby('g')['x'].mean() |
| egen y = total(x), by(g) | df.groupby('g')['x'].transform('sum') |
| gen / replace | df['y'] = ... / df.loc[条件, 'y'] = ... |
