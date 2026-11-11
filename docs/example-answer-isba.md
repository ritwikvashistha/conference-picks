# Example answer: ISBA 2026 World Meeting

The full answer from one run on 2026-11-11, copied as it came out: a Claude agent following the skill in a terminal, Standard budget. The user asked "I'm going to ISBA 2026. Its program is `isba2026_program.pdf`. My abstract is: ...", with ISBA's 193-page PDF program and the abstract of the paper in the NeurIPS example (148353). The agent stopped to ask for `pdftotext` to be installed, for the time zone (the book prints none) and for which of two clashing day headings was right, then imported 637 entries, showed the import report, waited for the user's OK, and searched. The [README](../README.md#other-conferences) links here. A different run, model or day can give different picks.

---

These picks come from the **2026 ISBA World Meeting** dataset, imported from your PDF program (snapshot 2026-11-11). The entries were cut out of the book by patterns, so a few may be wrong. **Your poster** looks like "Deconvolution using Empirical Bayes and Maximum Mean Discrepancy" (presenter Ritwik Vashistha), at Poster Session 2, Tue 2026-06-30 17:15–19:30. It was the top search hit and its topic matches your abstract, so I left it out of the ranking. Tell me if it isn't yours.

All times are Nagoya local time and come from the book's time blocks, not from individual talks. The book has no links, so each pick is cited by day, time, session and title. Only presenters are listed.

### Mon 2026-06-29 11:00
Multitrack Session 2 (11:00–12:30)
- **#19** Optimal Transport-Based Generative Models for Bayesian Posterior Sampling, by Yuexi Wang. Session: Bayesian Uncertainty Quantification and Posterior Sampling for Large-Scale Generative Models, Room 1101. It learns an optimal-transport generative map from a reference distribution, with adaptations for latent variable models. That is an alternative expressive generator to the normalizing flows in your sieve.

### Mon 2026-06-29 17:15
Poster Session I (17:15–19:30)
- **#4** Bayesian Empirical Bayes: Simultaneous Inference from Probabilistic Symmetries, by Bohan Wu. It extends empirical Bayes to latent variables that are not iid but structured (arrays, spatial processes, covariates). That is a natural next step for your learned-prior posterior denoising.
- **#6** Bernstein - von Mises theorem for the scale parameter in inverse problems, by Natalia Bochkina. It covers Bayesian linear inverse problems over Sobolev classes, with contraction rates that adapt to unknown smoothness. This is the same ill-posed inverse-problem rate theory behind your polynomial and logarithmic L2 rates.
- **#7** The minimax optimal convergence rate of posterior density in the weighted orthogonal polynomials, by Yiqi Luo. The dataset merged this title with the last lines of the previous abstract; the title here is the one the book prints. It builds priors that reach minimax n^(-p/(2p+1)) rates for Bayesian density estimation of mixture models in a weighted L2 framework. These are directly comparable to your L2 rates for the latent density.
- **#16** Bayesian Regression in the Proportional High-Noise Limit: A New Asymptotic Regime, by Satoru Tokuda. It gives Bayesian asymptotics when the measurement-noise variance grows with the sample size. That is the non-negligible-noise regime your abstract stresses.

### Tue 2026-06-30 11:00
Multitrack Sessions 4 (11:00–12:30)
- **#11** Generalized Bayesian inference for chaotic systems, by Antonietta Mira. Session: Deep Learning and Generalized Bayes, Room 1101. The likelihood is intractable, so it is replaced by losses on the discrepancy between observed and simulated attractors in an ill-posed inverse problem. That is a simulation-based discrepancy loss for the noisy "laws and dynamics of complex systems" your abstract opens with.

### Tue 2026-06-30 17:15
Poster Session 2 (17:15–19:30), the same slot as your poster
- **#5** Newton's algorithm as a gradient flow: a geometric framework for recursive mixture estimation, by Bernardo Flores. Same slot as your poster. It estimates a nonparametric mixture density (a latent mixing distribution under a kernel) by Newton's recursion, recast as a Fisher-Rao gradient flow. That is a fast competitor for learning the latent distribution, and a geometric view of your optimization.
- **#9** Learning the distance for ABC and neural posterior estimation, by Wang Yuyan. Same slot as your poster. It learns the distance between simulated and observed data for ABC and NPE. Choosing that discrepancy is the core design choice behind your convMMD objective.
- **#10** Posterior Attraction via Moment Matching: An MMD Minimization Approach, by Juan Maroñas. Same slot as your poster. It replaces KL with MMD minimization when no target density is available. That is the same reason you match distributions with MMD.
- **#14** Bayesian Multiplicative Errors-in-Variables Modeling for Hyperspectral Unmixing, by Vivek Kumar Singh. Same slot as your poster. It is an errors-in-variables model with multiplicative (log-normal) noise instead of additive homoscedastic noise. That is a measurement-error setting just outside your additive-noise assumption.

### Wed 2026-07-01 17:15
Poster Sessions 3 (17:15–18:30)
- **#13** Cluster Identification Through Minimum Distance Estimation, by Alexander Mozdzen. It minimizes a distance (sliced Wasserstein) between the empirical distribution and a mixture density, and stays consistent under misspecification. It is your idea of matching the observed distribution to a model distribution, with another distance and Gaussian mixtures.
- **#15** Particle methods for empirical Bayes, by Francesca Crucinio. It uses particle methods for marginal-maximum-likelihood empirical Bayes with latent variables, as an alternative to EM. That is the likelihood-based route to the empirical prior, which your likelihood-free method avoids.
- **#20** Empirical Bayes Shrinkage of Functional Effects, with Application to Analysis of Dynamic eQTLs, by Ziang Zhang. It shrinks effect functions across many units with a learned prior, in genomics. It is an applied empirical-Bayes denoising problem where a learned latent prior is the key ingredient.

### Thu 2026-07-02 09:00
Multitrack Sessions 8 (9:00–10:30)
- **#12** Hierarchical models as mixtures: identifiability and posterior contraction, by Long Nguyen. Session: Hierarchical Probabilistic Structures in BNP: Theoretical and Computational Advances, Main Hall. It covers identifiability and posterior contraction for mixture and hierarchical latent-variable models. These are the identifiability and rate questions for a latent distribution that your deconvolution theory faces.

### Thu 2026-07-02 11:00
Multitrack Sessions 9 (11:00–12:30). Session: Recent Advances in Neural Simulation-Based Inference, Room 1104
- **#8** Amortised and Provably-robust Simulation-based Inference, by Ayush Bharti. It does simulation-based inference with a generalized-Bayes weighted score-matching loss and is provably robust to outliers from faulty measurement. That is another discrepancy-based, likelihood-free objective for simulators with measurement error.
- **#18** Conservative neural posterior estimation via distributionally robust training, by Yuga Hikida. It trains normalizing-flow posteriors with a Wasserstein-robust loss to curb overconfidence under small simulation budgets. That is relevant to how you train flows with a simulation-based loss.

### Fri 2026-07-03 09:00
Multitrack Sessions 11 (9:00–10:30). Session: Advances in Nonparametric Empirical Bayes, Room 1102. Your three closest picks are in this one session.
- **#1** Compound decisions and empirical Bayes via Bayesian nonparametrics, by Sid Kankanala. In the Gaussian sequence compound decision problem, it shows that a Dirichlet-process Bayes procedure has near-optimal regret, benchmarked against the NPMLE. That is the theory of the empirical-Bayes denoising step you run with your learned prior.
- **#2** BNP Empirical Bayes. Consistency and efficiency in Robbins' framework, by Claudia Contardi. It is g-modelling empirical Bayes with a minimum-distance estimator under a Dirichlet-process prior, and asks for contraction rates of the estimated prior. That closely parallels your rates for a minimum-distance (convMMD) estimate of the latent density.
- **#3** Quasi-Bayes empirical Bayes: a sequential approach to the Poisson compound decision problem, by Sandra Fortini. It is a streaming estimate of the prior (Newton's algorithm), with consistency and regret guarantees. That is a cheap online alternative for your prior-learning step.

### Fri 2026-07-03 16:00
Multitrack Sessions 14 (16:00–17:30)
- **#17** Generalized Bayesian noise contrastive learning with additive tree ensembles, by Benedetta Bruni. Session: Advances in Bayesian Nonparametrics II, Room 1104. It learns densities for generative modeling with additive tree ensembles and a generalized-Bayes, noise-contrastive loss. That is another expressive density class trained without a likelihood, next to your Gaussian mixtures and flows.

**People worth talking to.** Nobody presents more than one pick, so these are the presenters of the picks closest to your work:
- Sid Kankanala (#1) and Claudia Contardi (#2): regret and contraction-rate theory for nonparametric empirical Bayes priors, which is the theory side of your denoising.
- Sandra Fortini (#3) and Bernardo Flores (#5): Newton-type recursive estimators of the latent mixing distribution, which are fast baselines for your prior estimate.
- Natalia Bochkina (#6) and Yiqi Luo (#7): rates for Bayesian inverse problems and minimax density rates, the setting of your L2 results.
- Ayush Bharti (#8): robust, discrepancy-based simulation-based inference.
- Bohan Wu (#4): empirical Bayes for structured latent variables.

**Your group's work:** no pick shares a presenter with your poster. The book lists only presenters, with no co-authors or affiliations, so this check is weak.

**Caveats.** The search pool is a fifth of the 637 entries (127 candidates). The times are those of each session block, not of individual talks.

Imported by you from isba2026_program.txt on 2026-11-11; the entries were cut out of the book's text by patterns, so a few may be wrong, and the book has no links (cite day, time, session and title): check the official program.
