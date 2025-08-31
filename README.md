# simple_homepage

## subtitle

### algorithm 
1) 프로젝트 목표 (한 줄)

5 / 20 / 60일 이동평균(MA)을 계산하고, WMA(감쇠) + EWMA(스무딩) 파라미터를 튜닝해서 MA의 편향(bias)과 잔차 분산(residual variance) 을 지표로 추세 신뢰도를 평가하는 것.

2) 데이터 & 전처리

데이터: 신세계(SHINSEGAE)와 S&P500 시계열 (Adj Close 우선 사용).

기간: 기본은 최근 10년(10y)으로 수집. (yfinance로 다운로드하거나 로컬 CSV 사용)

전처리: 날짜 파싱 → 정렬 → Adj Close 열 추출 → prices_adj.csv 생성.

생성한 파생파일: prices_with_sma.csv (*_SMA_5/_20/_60 컬럼 포함), price_df.csv (호환용), 원본 raw(SHINSEGAE_raw.csv, SP500_raw.csv) 저장.

3) 계산한 지표(정의)

MA: SMA(단순), WMA(가중; decay), optional EWMA(span).

Residual: 
𝑟
𝑡
=
𝑝
𝑡
−
𝑀
𝐴
^
𝑡
r
t
	​

=p
t
	​

−
MA
t
	​


Bias: 
𝑏
𝑡
=
rolling_mean
(
𝑟
𝑡
;
𝑤
)
b
t
	​

=rolling_mean(r
t
	​

;w) (w = window)

Residual std (variance indicator): 
𝑠
𝑡
=
rolling_std
(
𝑟
𝑡
;
𝑤
)
s
t
	​

=rolling_std(r
t
	​

;w)

Trend strength: slope(MA_smooth over window) / roll_std(price over window)

Score (튜닝 목적):

score
=
trend_median
resid_median
+
0.5
⋅
roll_median
+
0.7
⋅
bias_abs_median
score=
resid_median+0.5⋅roll_median+0.7⋅bias_abs_median
trend_median
	​

4) 튜닝 절차

탐색 파라미터
decay ∈ {0.8, 0.9, 0.92, 0.95, 0.98}, ewma_span ∈ {None, 3, 5, 8}

윈도우: 5, 20, 60 (각각 따로 튜닝)

각 조합에 대해 trend_median, resid_std_median, roll_std_median, bias_abs_median 계산 → score 계산 → Top-N 저장.

출력: tune_{ASSET}_w{W}.csv (모든 조합 결과), 최적값을 이용해 플롯 저장(Price + tuned WMA, bias, resid_std).

5) 주요 산출물(파일)

CSVs:

./data/prices_adj.csv

./data/prices_with_sma.csv

./data/price_df.csv

./data/ten_year_data/tune_SHINSEGAE_w5.csv, ..._w20.csv, ..._w60.csv (또는 ./data/tuning_results/...)

./data/ten_year_data/summary_metrics_10y_5_60.csv

PNGs (예):

./data/ten_year_plots/SHINSEGAE_price_wma20.png

./data/ten_year_plots/SHINSEGAE_bias20.png

./data/ten_year_plots/SHINSEGAE_residstd20.png

동일 구조의 SP500 플롯, plus *_w5_best.png, *_w60_best.png 등

Word 보고서: MA_report_shinsegae_sp500.docx (초안 생성)

(파일 경로는 네 환경/스크립트에서 지정한 위치에 따라 달라질 수 있음 — 위는 생성 스크립트 기준)

6) 핵심 결과(네 실행 결과 기준)

두 자산 모두 score 기준으로는 window=5(단기)가 가장 높은 score로 나옴.

예시(화면값):

SHINSEGAE best window=5, score ≈ 6.1054e-05, trend_median≈0.3201, resid_median≈2510.4, bias_median≈1572.65

SP500 best window=5, score ≈ 0.00888458, trend_median≈0.3374, resid_median≈17.75, bias_median≈11.61

이유(해석): trend_median이 5일에서 상대적으로 크게 나오고, score 분모(잔차·롤·바이어스)가 상대적으로 작게 잡혀서 5일이 유리하게 평가됨.

주의: 5일은 반응이 빠르지만 노이즈/과적합 위험이 큼 → 단순 score만으로 최종 선택하면 안 됨.

7) 간단한 해석 가이드 (보고서에 쓸 한두 문장)

“튜닝 결과 score 기준으로는 단기(5일) MA가 최고였으나, 5일 MA는 잦은 단기 변동에 민감하므로 실전 적용 시 residual_std 기반 필터(예: residual_std < 2% of mean price) 및 OOS(Out-of-sample) 검증을 병행해야 한다.”

“S&P500은 절대치 기준으로 residual·bias가 작아 동일 규칙에서 비교적 안정적인 반면, SHINSEGAE는 절대 가격 단위가 커서 % 정규화하여 해석해야 한다.”

8) 권장 개선·검증 절차 (우선순위)

정규화 기반 비교: 결과(잔차·바이어스)를 %로 표기(평균가격으로 나눈 값) — 자산 간 비교에서 필수.

OOS / Rolling-tune: (예) 과거 7년(튜닝) / 최근 3년(검증) 또는 롤링: 3년 튜닝 → 다음 1년 테스트를 반복.

임계치 필터 적용: 잔차 표준편차가 X%(권장: 1~2%)를 넘는 기간엔 신호 무시. 자동 임계치 제안: resid_pct의 75% 백분위수 사용.

Top-3 비교 플롯: Top-3 파라미터의 WMA를 한 그래프에 겹쳐 비교(시간축 시각화).

간단 백테스트: 룰(진입: 5/20 골든 + resid_std < threshold 등)로 샘플 백테스트(수수료·슬리피지 포함).

9) 제출용(보고서에 바로 붙여넣을 문단)

(요약문 — 복사해서 붙여넣기)

본 실험에서는 SHINSEGAE와 S&P500의 조정종가를 사용해 5, 20, 60일 이동평균을 계산하고, WMA의 감쇠계수(decay) 및 EWMA 스팬을 그리드로 튜닝하여 MA 대비 residual의 bias 및 표준편차를 지표로 비교하였다. 튜닝 평가지표는 trend_strength_median을 분자로 하고 residual_std_median·roll_std_median·bias_abs_median의 가중합을 분모로 하는 score를 사용하였다. 결과적으로 score 기준에서는 단기(5일) MA가 높게 평가되었으나, 단기 MA는 노이즈에 민감하므로 실전 적용 전 OOS 검증 및 residual_std 기반 필터 적용을 권장한다.

(결론·권장 — 복사)

결론: score 기준으로는 5일 MA가 우수했으나 안정성을 위해 20/60일 MA와 병행한 다중확증(멀티타임프레임), 잔차 기반 필터링, OOS 백테스트를 반드시 수행해야 한다.
