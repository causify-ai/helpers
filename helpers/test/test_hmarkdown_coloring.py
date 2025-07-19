import logging

import helpers.hmarkdown as hmarkdo
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_colorize_bullet_points1
# #############################################################################


class Test_colorize_bullet_points_in_slide1(hunitest.TestCase):
    def test1(self) -> None:
        text = """
        * Machine Learning Flow

        ::: columns
        :::: {.column width=90%}
        - Question
        - E.g., "How can we predict house prices?"
        - Input data
        - E.g., historical data of house sales

        - _"If I were given one hour to save the planet, I would spend 59 minutes
        defining the problem and one minute resolving it"_ (Albert Einstein)

        - **Not all phases are equally important!**
        - Question $>$ Data $>$ Features $>$ Algorithm
        - Clarity of the question impacts project success
        - Quality and relevance of data are crucial for performance
        - Proper feature selection simplifies the model and improves accuracy
        - Algorithm is often less important (contrary to popular belief!)
        ::::
        :::: {.column width=5%}

        ```graphviz[height=90%]
        digraph BayesianFlow {
            rankdir=TD;
            splines=true;
            ...
        }
        ```
        ::::
        :::
        """
        expected = """
        * Machine Learning Flow

        ::: columns
        :::: {.column width=90%}
        - Question
        - E.g., "How can we predict house prices?"
        - Input data
        - E.g., historical data of house sales

        - _"If I were given one hour to save the planet, I would spend 59 minutes
        defining the problem and one minute resolving it"_ (Albert Einstein)

        - **\\red{Not all phases are equally important!}**
        - Question $>$ Data $>$ Features $>$ Algorithm
        - Clarity of the question impacts project success
        - Quality and relevance of data are crucial for performance
        - Proper feature selection simplifies the model and improves accuracy
        - Algorithm is often less important (contrary to popular belief!)
        ::::
        :::: {.column width=5%}

        ```graphviz[height=90%]
        digraph BayesianFlow {
            rankdir=TD;
            splines=true;
            ...
        }
        ```
        ::::
        :::
        """
        act = hmarkdo.colorize_bullet_points_in_slide(text)
        # Check output.
        self.assert_equal(act, expected)