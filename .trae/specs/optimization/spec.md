# NBA奖项客观数据标准评选技能 - 优化需求文档

## Overview
- **Summary**: 当前NBA奖项评选技能无法使用，因为核心数据获取脚本中的关键函数均为空实现。需要完善Python数据获取脚本，实现多数据源数据获取、交叉验证和奖项评选算法。
- **Purpose**: 修复技能不可用问题，使其能够真正实现基于客观数据的NBA奖项评选功能。
- **Target Users**: 需要进行NBA奖项数据分析和历史重评的用户

## Goals
- 实现完整的数据获取功能（支持 nba_api、balldontlie、Basketball-Reference）
- 实现多数据源交叉验证逻辑
- 实现常规赛奖项评选算法（MVP/DPOY/最佳阵容等）
- 实现季后赛奖项评选算法（总冠军/FMVP/季后赛MVP）
- 实现总冠军含金量指数(CQI)计算
- 支持结果导出为Markdown文件

## Non-Goals (Out of Scope)
- 不开发Web界面
- 不实现实时数据更新
- 不支持非英语语言

## Background & Context
- 当前 `SKILL.MD` 定义了完整的奖项评选规则和工作流
- `nba_data_fetcher.py` 仅有框架但无实际实现
- 需要补充数据获取、交叉验证、奖项评选的完整逻辑

## Functional Requirements
- **FR-1**: 支持从 nba_api 获取球员基础数据和高阶数据
- **FR-2**: 支持从 balldontlie API 获取球员数据
- **FR-3**: 实现多数据源交叉验证逻辑
- **FR-4**: 实现常规赛奖项评选（数据王、MVP、DPOY、最佳阵容等）
- **FR-5**: 实现季后赛奖项评选（总冠军、FMVP、季后赛MVP）
- **FR-6**: 实现CQI总冠军含金量指数计算
- **FR-7**: 支持将评选结果导出为Markdown文件

## Non-Functional Requirements
- **NFR-1**: 数据源优先级：Basketball-Reference > nba_api > balldontlie > 虎扑
- **NFR-2**: 数据差异>10%时需标注警告
- **NFR-3**: 缺失指标降级为PER+WS/48加权

## Constraints
- **Technical**: Python 3.8+, 依赖 nba_api, balldontlie, requests, beautifulsoup4
- **Dependencies**: 需安装外部库：pip install nba-api balldontlie requests beautifulsoup4 pandas

## Assumptions
- 用户已安装Python环境
- 用户可访问外部API（nba_api、balldontlie）
- Basketball-Reference网站结构稳定

## Acceptance Criteria

### AC-1: 数据获取功能正常
- **Given**: 输入有效赛季（如2024）
- **When**: 运行数据获取脚本
- **Then**: 成功获取球队排名和球员高阶数据
- **Verification**: `programmatic`

### AC-2: 交叉验证正常工作
- **Given**: 多个数据源返回不同数据
- **When**: 执行交叉验证
- **Then**: 输出置信度标记（高/中/低）
- **Verification**: `programmatic`

### AC-3: MVP评选正确
- **Given**: 完整的赛季数据
- **When**: 执行MVP评选算法
- **Then**: 按战绩分60%+高阶数据分40%计算排名
- **Verification**: `human-judgment`

### AC-4: DPOY评选正确
- **Given**: 完整的赛季数据
- **When**: 执行DPOY评选算法
- **Then**: 基于DBPM、DWS、抢断+盖帽归一化得分
- **Verification**: `human-judgment`

### AC-5: 季后赛MVP评选正确
- **Given**: 季后赛数据
- **When**: 执行季后赛MVP评选
- **Then**: 按轮次赋分+高阶数据计算
- **Verification**: `human-judgment`

### AC-6: CQI计算正确
- **Given**: 总冠军相关数据
- **When**: 执行CQI计算
- **Then**: 输出正确的含金量指数和评级
- **Verification**: `programmatic`

### AC-7: 结果导出正常
- **Given**: 评选完成
- **When**: 用户选择导出
- **Then**: 生成Markdown格式报告文件
- **Verification**: `programmatic`

## Open Questions
- [ ] 是否需要支持更早的历史赛季（如1980年前）？
- [ ] 是否需要添加更多数据源？
