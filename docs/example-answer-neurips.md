# Example answer: NeurIPS 2026

The full answer from one run on 2026-11-11, copied as it came out: Claude Code, Standard budget, asked "I'm going to NeurIPS 2026. My paper there is id 148353. Which papers should I see?" The [README](../README.md#use-it) quotes its start. A different run, model or day can give different picks.

---

Your paper, [Noisy2Latent: Nonparametric Deconvolution and Denoising via Maximum Mean Discrepancy](https://neurips.cc/virtual/2026/poster/148353) (148353), is presented at **Sydney Tue 2026-12-08 10:00**.

Budget: Standard, since I could not ask you to choose. I triaged 150 keyword candidates by title and matched terms, then read the first 700 characters of 34 abstracts. That costs about 35K tokens on top of the session's baseline (measured in test runs; yours may differ). Quick (ranked list only, a few K) and Deep (all 150 abstracts, about 115K) are the alternatives.

20 picks, ranked #1 to #20, grouped by site and session.

## Sydney

### Sydney Tue 2026-12-08 10:00
- **#5** [Bridging the Simulation-to-Experiment Gap with Adversarial Distribution Alignment](https://neurips.cc/virtual/2026/poster/151598): Kai Nelson, Tobias Kreiman, Sergey Levine, Aditi Krishnapriyan. They align a generative model with experimental data that only partly observe the system's state, so the model is fitted through an observation process. You do the same when you match the observed data to the noise-convolved model. **Same slot as your poster.**

### Sydney Tue 2026-12-08 17:00
- **#3** [Sobolev Regularized MMD Gradient Flow](https://neurips.cc/virtual/2026/poster/152622): Chenyang Tian, Bharath Sriperumbudur, Arthur Gretton, Zonghao Chen. A gradient penalty on the MMD witness function gives provable global convergence when minimizing MMD. Your finite-sample bounds are for empirical sieve minimizers, and this work addresses when an optimizer of an MMD objective actually reaches the minimizer.
- **#18** [Kernel Selection is Model Selection: A Unified Complexity-Penalised Approach for MMD Two-Sample Tests](https://neurips.cc/virtual/2026/poster/153658): Yijin Ni, Xiaoming Huo. The kernel decides which distributions MMD can tell apart, and this paper chooses it with a complexity penalty. That bears on the kernel inside your convMMD loss.

### Sydney Wed 2026-12-09 10:00
- **#4** [Energy-Tweedie: Score meets Score, Energy meets Energy](https://neurips.cc/virtual/2026/poster/150007): Andrej Leban. Extends Tweedie's formula, the classical link between posterior-mean denoising and the score of the noisy marginal, from Gaussian to generalized-Gaussian and other elliptical noise. It is another route to the posterior denoising you do with a learned empirical prior.
- **#16** [Tunable Latent Generative Priors for Compressed Sensing and Inverse Problems](https://neurips.cc/virtual/2026/poster/149979): Sean Gunn, Jorio Cocola, Paul Hand, Oliver De Candido, Vaggos Chatziafratis. They make the complexity of latent generative priors (normalizing flows among them) tunable, because a latent dimension that is too large overfits the noise. That is the same trade-off as choosing the size of your sieve.

### Sydney Wed 2026-12-09 17:00
- **#2** [Empirical Bayes Rebiasing](https://neurips.cc/virtual/2026/poster/152794): Wanyi Ling, Sida Li, Junming Guan, Nikolaos Ignatiadis. They estimate an unknown bias distribution from many noisy estimates and use it to build calibrated intervals. It is a deconvolution-style empirical Bayes problem, close to your step of using the learned density as a prior, approached from classical empirical Bayes.
- **#13** [Calibrating Generative Models to Feature Distributions with MMD Finetuning](https://neurips.cc/virtual/2026/poster/148368): Nathaniel L. Diamant, Brian L Trippe. They finetune expressive generative models with a kernel MMD objective so that chosen feature distributions match a reference set. MMD is the training loss for a generative model here, as convMMD is in your paper.
- **#20** [Extended Wasserstein-GAN Approach to Causal Distribution Learning: Density-Free Estimation and Minimax Optimality](https://neurips.cc/virtual/2026/poster/149316): Shu Tamano, Masaaki Imaizumi. A density-free (Wasserstein-GAN) estimator of interventional distributions with minimax-optimality results. Like yours, it is a likelihood-free distribution estimator with rates, here in causal inference.

### Sydney Thu 2026-12-10 10:00
- **#1** [Empirical Bayes Flow Matching for Continuous Cryo-EM Heterogeneity](https://neurips.cc/virtual/2026/poster/151539): Daniel Aibinder, Azmi Haider, Dan Rosenbaum. They learn a flow-matching prior over latent variables directly from indirect, noisy observations (cryo-EM projections), inside a Monte Carlo EM framework. Your paper has the same goal: learn the latent distribution from noisy data and use it as a prior. Theirs takes a likelihood-based EM route with a non-linear forward operator, where yours uses a likelihood-free convMMD loss under additive noise.
- **#7** [Reversing the Roles of Signal and Noise: Modeling Noise in Astronomical Images without Paired Data](https://neurips.cc/virtual/2026/poster/150362): Drew Tufto, Daniel Muthukrishna. They learn a generative model of the clean signal and use it to score noise estimates, with no clean and noisy pairs ever observed. That is the no-ground-truth separation of signal from instrument noise that motivates Noisy2Latent, applied to astronomical images.
- **#14** [Nonparametric Estimation of a Factorizable Density using Diffusion Models](https://neurips.cc/virtual/2026/poster/156671): Hyeok Kyu Kwon, Dongha Kim, Ilsang Ohn, Minwoo Chae. They treat diffusion models as nonparametric density estimators and analyze them statistically, using low-dimensional (factorizable) structure. This is the estimation-theory side of your sieve analysis, for a different generative class.

### Sydney Thu 2026-12-10 17:00
- **#17** [Exact Posterior Score Estimation for Solving Linear Inverse Problems](https://neurips.cc/virtual/2026/poster/155154): Abbas Mammadov, Ozgur Kara, Kaan Oktay, Iskander Azangulov, Adil K Akan, Hyungjin Chung, James Rehg, Yee Whye Teh. They derive the exact posterior score in closed form for linear Gaussian inverse problems with diffusion or flow priors. Additive Gaussian noise is the identity-operator case, so this is a diffusion-prior alternative to your posterior denoising step.

## Atlanta

### Atlanta Wed 2026-12-09 16:30
- **#19** [Minimax Optimal Kernel Two-sample Testing in Sub-quadratic Time](https://neurips.cc/virtual/2026/poster/149505): Ikjun Choi, Shourya Pandey, Purnamrita Sarkar. They approximate MMD in sub-quadratic time and keep minimax-optimal power. This could cut the quadratic kernel cost of an MMD-type loss like yours on large samples. The authors are at UT Austin, like you.

### Atlanta Thu 2026-12-10 10:00
- **#11** [Inference and estimation with unidentifiable latent treatment effects](https://neurips.cc/virtual/2026/poster/154647): Christopher Tosh, Boyuan Zhang, Wesley Tansey. They extend the classical two-groups empirical Bayes model to latent, confounded treatment effects. Like your paper, it infers a latent effect distribution from noisy outcomes.

### Atlanta Fri 2026-12-11 10:00
- **#8** [Attention as In-Context Empirical Bayes: A Two-Stage View via Particle Dynamics](https://neurips.cc/virtual/2026/poster/149497): Matthew Smart, Soumya Ganguly, Nilava Metya, Alexandre V Morozov, Anirvan Sengupta. They show that one attention step computes a kernel-weighted posterior mean under the empirical distribution of the context, which makes it an empirical Bayes denoiser of corrupted tokens. Worth comparing with your empirical-prior posterior denoising.

### Atlanta Fri 2026-12-11 16:30
- **#6** [Bias, Measurement Error, and Double-Dipping: When Can GNN Convolutions Help Brain Connectome Prediction?](https://neurips.cc/virtual/2026/poster/153204): Tommaso Castellani, Jiaqi Li, Muriah D Wheelock, Rezwana R Razzaque, Helmut Laufs, Hong Chen, Claire Donnat. They cast connectome prediction as an errors-in-variables problem, with the true connectome latent and the observed correlation matrix a noisy estimate, and use it to explain why GNNs fail there. It is an applied measurement-error setting, close to the problem your method addresses.
- **#10** [DnNP: Denoising Input Uncertainty in Neural Processes](https://neurips.cc/virtual/2026/poster/149321): Fatemeh Tohidian, Chengzhi Shi, Soomi Lee, Matthew Elia, Amy V Mueller, Stratis Ioannidis, Jennifer Dy. Neural processes that model inputs observed with sensor or measurement error, trained by variational inference. These are errors-in-variables on the input side, in contrast to your likelihood-free deconvolution.

## Paris

### Paris Wed 2026-12-09 17:00
- **#9** [Robust Amortized Simulation-Based Inference via Learned Error Models](https://neurips.cc/virtual/2026/poster/151610): Matthew O'Callaghan, Kaisey Mandel, Gerard Gilmore. Using multiple unlabeled observations, they jointly learn a misspecification-robust posterior and an explicit error model inside simulation-based inference. It is another likelihood-free way to handle the gap between a model and noisy scientific data.

### Paris Thu 2026-12-10 12:30
- **#12** [Generative Modeling under Non-Monotone MAR Missingness via Approximate Wasserstein Gradient Flows](https://neurips.cc/virtual/2026/poster/155457): Gitte Kremling, Jeffrey Näf, Johannes Lederer. They recover the full-data distribution from incomplete (MAR) data with a nonparametric method that fits the observed-data distribution. Your paper rests on the same idea: fit the latent distribution so that its corrupted version matches what is observed. Here the corruption is missingness rather than additive noise.

### Paris Thu 2026-12-10 17:30
- **#15** [Difference of Convex Programming in the Wasserstein Space with Applications to MMD Optimization](https://neurips.cc/virtual/2026/poster/148506): Clément Bonet, Pierre-Cyril Aubin-Frankowski, Youssef Mroueh. They lift the convex-concave procedure to Wasserstein space, with MMD optimization as the application. It gives optimization guarantees for non-convex MMD objectives over probability measures, which matters when you minimize the convMMD loss.

## Authors worth talking to
No author appears on more than one pick, so these are authors of the picks closest to your work:
- **Dan Rosenbaum** (#1): learning priors from indirect noisy observations with flow matching and EM, a likelihood-based counterpart to Noisy2Latent.
- **Nikolaos Ignatiadis** (#2): empirical Bayes with an unknown, estimated distribution of biases, close to your empirical-prior denoising.
- **Arthur Gretton** and **Bharath Sriperumbudur** (#3): convergence guarantees for MMD minimization with Sobolev regularization, relevant to optimizing and analyzing convMMD.
- **Andrej Leban** (#4, sole author): Tweedie-style denoising beyond Gaussian noise.
- **Claire Donnat** (#6): errors-in-variables modeling of noisy connectome estimates, a possible application of your method.
- **Daniel Muthukrishna** (#7): separating signal from instrument noise without ground truth in astronomy.
- **Kaisey Mandel** (#9): learned error models for likelihood-free inference on scientific data.

Not ranked because they share an author with your paper (your group's work): [Don't Match the Noise: Distribution Matching under Unknown Measurement Error with an Audit Sample](https://neurips.cc/virtual/2026/poster/153320) (Arya Farahi, Ritwik Vashistha; Sydney Tue 2026-12-08 10:00, same slot as your poster) and [Robust-by-Design Distributional Learning from Contaminated Samples](https://neurips.cc/virtual/2026/poster/154903) (Nevena Gligić, Arya Farahi; Paris Fri 2026-12-11 14:30).

Times come from a snapshot of the NeurIPS 2026 program (event list of 2026-11-05, schedule file of 2026-11-04, per `DATA_NOTICE.md`) and may have changed; check neurips.cc for the official schedule.
