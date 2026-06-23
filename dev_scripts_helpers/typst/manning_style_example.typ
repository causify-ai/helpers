// Import Manning style formatting and macros
#import "manning_style.typ": manning-style, chapter, chapter-intro, fact-box, section-heading, term

// Document metadata
#set document(
  title: "Probabilistic Machine Learning",
  author: "ML Education",
)

// Apply the Manning document template (page/text/heading set + show rules)
#show: manning-style

// Main document
#chapter("2", "Bayesian Inference and Posterior Estimation")

// Chapter introduction
#chapter-intro[
  - Understanding Bayes' theorem and posterior distributions
  - Variational inference and approximate inference methods
  - Practical applications in probabilistic modeling
]

#v(0.8em)

== Bayes' Theorem and Posterior Computation

#fact-box[
  Bayes' theorem relates the posterior distribution $p(theta | D)$ to the
  likelihood and prior: $p(theta | D) = (p(D | theta) p(theta)) / p(D)$
]

The fundamental problem in Bayesian inference is computing the #term[posterior
distribution], which represents our updated beliefs about model parameters given
observed data. The posterior combines:

- *Prior* $p(theta)$: our initial beliefs about parameters
- *Likelihood* $p(D | theta)$: how well parameters explain the data
- *Evidence* $p(D)$: normalizing constant to ensure distribution sums to 1

=== Maximum A Posteriori (MAP) Estimation

In many practical applications, we seek a point estimate rather than the full
posterior. #term[Maximum A Posteriori] estimation finds the mode of the posterior:

$$theta_(M A P) = max_(theta) p(theta | D)$$

This balances data fit (likelihood) with prior regularization, making it robust
to overfitting compared to maximum likelihood estimation.

=== Example: Coin Flip Inference

Consider inferring the bias $theta$ of a coin. We observe $n$ flips with $k$
heads. Using a Beta prior $"Beta"(alpha, beta)$:

- *Prior*: $p(theta) = "Beta"(alpha, beta)$
- *Likelihood*: $p(D | theta) = theta^k (1 - theta)^(n-k)$
- *Posterior*: $p(theta | D) = "Beta"(alpha + k, beta + n - k)$

The posterior is also Beta distributed, making this a #term[conjugate prior]
example. The posterior mean is:

$$E[theta | D] = (alpha + k) / (alpha + beta + n)$$

== Variational Inference

#fact-box[
  Variational inference approximates an intractable posterior $p(z | x)$ with a
  tractable distribution $q(z)$ by minimizing the KL divergence: $min_q
  "KL"(q(z) || p(z | x))$
]

When the posterior is too complex to compute analytically, we turn to #term[variational
inference]. Instead of computing the true posterior, we search for an
approximate posterior $q(z)$ from a tractable family (e.g., Gaussian or factorized
distributions).

The key insight is that minimizing $"KL"(q || p)$ is equivalent to maximizing
the Evidence Lower Bound (ELBO):

$$"ELBO"(q) = E_q [log p(x, z)] - E_q [log q(z)]$$

=== Mean-Field Variational Inference

A common choice is #term[mean-field] approximation, where we assume all
latent variables are independent:

$$q(z) = product_(i=1)^K q_(i)(z_i)$$

This factorization makes inference tractable but sacrifices some accuracy by
ignoring correlations between variables.

#pagebreak()

== Model Comparison and Hyperparameter Selection

#fact-box[
  Model evidence (marginal likelihood) $p(D) = integral p(D | theta) p(theta) dif theta$
  provides principled model selection that automatically penalizes complexity.
]

When choosing between competing probabilistic models, we can use the model
evidence:

$$p(D | M) = integral p(D | theta, M) p(theta | M) dif theta$$

Models with higher evidence are preferred. This criterion automatically balances
goodness of fit and model complexity—a phenomenon known as #term[Occam's razor]
in the Bayesian framework.

The log model evidence can be approximated using:
- Laplace approximation
- Variational lower bound
- Bridge sampling

== Summary

Bayesian inference provides a principled framework for learning from data:

- *Posterior computation* integrates prior beliefs with observed evidence
- *Variational methods* enable approximate inference when exact computation is
  intractable
- *Model evidence* offers automatic complexity penalization for model selection

These techniques form the foundation for advanced probabilistic models including
Gaussian processes, topic models, and deep generative models.
