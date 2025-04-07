import logging
import os
import pprint

import pytest

import dev_scripts_helpers.documentation.render_images as dshdreim
import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_get_rendered_file_paths1
# #############################################################################


class Test_get_rendered_file_paths1(hunitest.TestCase):

    def test1(self) -> None:
        """
        Check generation of file paths for rendering images.
        """
        # Prepare inputs.
        out_file = "/a/b/c/d/e.md"
        image_code_idx = 8
        dst_ext = "png"
        # Run function.
        paths = dshdreim._get_rendered_file_paths(
            out_file, image_code_idx, dst_ext
        )
        # Check output.
        act = "\n".join(paths)
        exp = """
        tmp.render_images/e.8.txt
        /a/b/c/d/figs
        figs/e.8.png
        """
        self.assert_equal(act, exp, dedent=True)


# #############################################################################
# Test_ImageHashCache1
# #############################################################################


class Test_ImageHashCache1(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test basic functionality of ImageHashCache.
        """
        # Create a temporary cache file.
        cache_file = os.path.join(
            self.get_scratch_space(), "image_hash_cache.json"
        )
        # Initialize cache.
        cache = dshdreim.ImageHashCache(cache_file)
        # Test initial state.
        self.assertEqual(cache.cache, {})
        # Test computing hash.
        image_code = "digraph { A -> B }"
        image_code_type = "graphviz"
        out_file = "/tmp/test.png"
        hash_key, cache_value = cache.compute_hash(
            image_code, image_code_type, out_file
        )
        # Verify the cache value structure.
        act = pprint.pformat(cache_value)
        exp = """
        {'image_code_hash': 'f068f0efa138e56c739c1b9f8456c312f714f96488204242c73f4ce457236f88',
         'image_code_type': 'graphviz',
         'out_file': '/tmp/test.png'}
        """
        self.assert_equal(act, exp, dedent=True)
        # Update the cache.
        cache_updated = cache.update_cache(hash_key, cache_value)
        # There should be an update since the cache is empty.
        self.assertTrue(cache_updated)
        # Check the content of the cache file.
        act = hio.from_file(cache_file)
        exp = r"""
        {
            "/tmp/test.png": {
                "image_code_hash": "f068f0efa138e56c739c1b9f8456c312f714f96488204242c73f4ce457236f88",
                "image_code_type": "graphviz",
                "out_file": "/tmp/test.png"
            }
        }"""
        self.assert_equal(act, exp, dedent=True)
        # 2) Perform a second update without changing the cache value.
        cache_updated = cache.update_cache(hash_key, cache_value)
        # No update should happen since the value is the same.
        self.assertFalse(cache_updated)
        # 3) Perform a third update with a different cache value.
        image_code = "new image code"
        image_code_type = "graphviz"
        out_file = "/tmp/test.png"
        hash_key, cache_value = cache.compute_hash(
            image_code, image_code_type, out_file
        )
        # Verify the cache value structure.
        act = pprint.pformat(cache_value)
        exp = """
        {'image_code_hash': 'e28869819b0fb5b24a37cec1f0f05190b622d1c696fdc43de5c79026f07bb869',
         'image_code_type': 'graphviz',
         'out_file': '/tmp/test.png'}
        """
        self.assert_equal(act, exp, dedent=True)
        # Update the cache.
        cache_updated = cache.update_cache(hash_key, cache_value)
        self.assertTrue(cache_updated)
        # Check the content of the cache file.
        act = hio.from_file(cache_file)
        exp = r"""
        {
            "/tmp/test.png": {
                "image_code_hash": "e28869819b0fb5b24a37cec1f0f05190b622d1c696fdc43de5c79026f07bb869",
                "image_code_type": "graphviz",
                "out_file": "/tmp/test.png"
            }
        }"""
        self.assert_equal(act, exp, dedent=True)
        # 4) Update the cache with a different key.
        image_code = "new image code 2"
        image_code_type = "graphviz"
        out_file = "/tmp/test2.png"
        hash_key, cache_value = cache.compute_hash(
            image_code, image_code_type, out_file
        )
        # Update the cache.
        cache_updated = cache.update_cache(hash_key, cache_value)
        # There should be an update since the cache is empty.
        self.assertTrue(cache_updated)
        # Check the content of the cache file.
        act = hio.from_file(cache_file)
        exp = r"""
        {
            "/tmp/test.png": {
                "image_code_hash": "e28869819b0fb5b24a37cec1f0f05190b622d1c696fdc43de5c79026f07bb869",
                "image_code_type": "graphviz",
                "out_file": "/tmp/test.png"
            },
            "/tmp/test2.png": {
                "image_code_hash": "ffc71f5ebd6f0df6d0fafe70a87413096d5498f90353c0f8a1908e18656b8de9",
                "image_code_type": "graphviz",
                "out_file": "/tmp/test2.png"
            }
        }"""
        self.assert_equal(act, exp, dedent=True)


# #############################################################################
# Test_render_image_code1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci(), reason="Disabled because of CmampTask10710"
)
class Test_render_image_code1(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test rendering a basic image code block.
        """
        is_cache_hit = self._get_test_render_image_code_inputs1(use_cache=True)
        # Check output.
        self.assertFalse(is_cache_hit)

    def test2(self) -> None:
        """
        Test rendering with cache.
        """
        # 1) New computation -> cache miss.
        is_cache_hit = self._get_test_render_image_code_inputs1(use_cache=True)
        self.assertFalse(is_cache_hit)
        # 2) Same as 1) -> cache hit.
        is_cache_hit = self._get_test_render_image_code_inputs1(use_cache=True)
        self.assertTrue(is_cache_hit)
        # 3) Different image code -> cache miss.
        is_cache_hit = self._get_test_render_image_code_inputs2(use_cache=True)
        self.assertTrue(is_cache_hit)
        # 4) Different file -> cache miss.
        is_cache_hit = self._get_test_render_image_code_inputs3(use_cache=True)
        # Check output.
        self.assertFalse(is_cache_hit)
        # 5) Same as 3) -> cache hit.
        is_cache_hit = self._get_test_render_image_code_inputs2(use_cache=True)
        self.assertTrue(is_cache_hit)
        # 6) Same as 4) -> cache hit.
        is_cache_hit = self._get_test_render_image_code_inputs3(use_cache=True)
        self.assertTrue(is_cache_hit)

    def test3(self) -> None:
        """
        Test rendering without cache.

        There are only cache misses when rendering without cache.
        """
        # 1) New computation.
        is_cache_hit = self._get_test_render_image_code_inputs1(use_cache=False)
        self.assertFalse(is_cache_hit)
        # 2) Same as 1).
        is_cache_hit = self._get_test_render_image_code_inputs1(use_cache=False)
        self.assertFalse(is_cache_hit)
        # 3) Different image code.
        is_cache_hit = self._get_test_render_image_code_inputs2(use_cache=False)
        self.assertFalse(is_cache_hit)
        # 4) Different file.
        is_cache_hit = self._get_test_render_image_code_inputs3(use_cache=False)
        # Check output.
        self.assertFalse(is_cache_hit)
        # 5) Same as 3).
        is_cache_hit = self._get_test_render_image_code_inputs2(use_cache=False)
        self.assertFalse(is_cache_hit)
        # 6) Same as 4).
        is_cache_hit = self._get_test_render_image_code_inputs3(use_cache=False)
        self.assertFalse(is_cache_hit)

    def _get_test_render_image_code_inputs1(self, use_cache: bool) -> bool:
        """
        Run `render_image_code()` function.
        """
        # Prepare inputs.
        image_code = "digraph { A -> B }"
        image_code_idx = 1
        image_code_type = "graphviz"
        template_out_file = os.path.join(self.get_scratch_space(), "test.md")
        dst_ext = "png"
        cache_file = os.path.join(
            self.get_scratch_space(), "image_hash_cache.json"
        )
        # Run function.
        rel_img_path, is_cache_hit = dshdreim._render_image_code(
            image_code,
            image_code_idx,
            image_code_type,
            template_out_file,
            dst_ext,
            use_cache=use_cache,
            cache_file=cache_file,
        )
        # Check output.
        self.assertEqual(rel_img_path, "figs/test.1.png")
        return is_cache_hit

    def _get_test_render_image_code_inputs2(self, use_cache: bool) -> bool:
        """
        Same file as `example1` but different image code.
        """
        # Prepare inputs.
        image_code = "digraph { B -> A }"
        image_code_idx = 1
        image_code_type = "graphviz"
        template_out_file = os.path.join(self.get_scratch_space(), "test.md")
        dst_ext = "png"
        cache_file = os.path.join(
            self.get_scratch_space(), "image_hash_cache.json"
        )
        # Run function.
        rel_img_path, is_cache_hit = dshdreim._render_image_code(
            image_code,
            image_code_idx,
            image_code_type,
            template_out_file,
            dst_ext,
            use_cache=use_cache,
            cache_file=cache_file,
        )
        # Check output.
        self.assertEqual(rel_img_path, "figs/test.1.png")
        return is_cache_hit

    def _get_test_render_image_code_inputs3(self, use_cache: bool) -> bool:
        """
        Different file than `example1` and `example2`.
        """
        # Prepare inputs.
        image_code = "digraph { A -> B }"
        image_code_idx = 1
        image_code_type = "graphviz"
        template_out_file = os.path.join(self.get_scratch_space(), "test2.md")
        dst_ext = "png"
        cache_file = os.path.join(
            self.get_scratch_space(), "image_hash_cache.json"
        )
        # Run function.
        rel_img_path, is_cache_hit = dshdreim._render_image_code(
            image_code,
            image_code_idx,
            image_code_type,
            template_out_file,
            dst_ext,
            use_cache=use_cache,
            cache_file=cache_file,
        )
        # Check output.
        self.assertEqual(rel_img_path, "figs/test2.1.png")
        return is_cache_hit


# #############################################################################
# Test_render_images1
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci(), reason="Disabled because of CmampTask10710"
)
class Test_render_images1(hunitest.TestCase):
    """
    Test _render_images() with dry run enabled (updating file text without
    creating images).
    """

    def helper(self, txt: str, file_ext: str, exp: str) -> None:
        """
        Check that the text is updated correctly.

        :param txt: the input text
        :param file_ext: the extension of the input file
        """
        # Prepare inputs.
        txt = hprint.dedent(txt, remove_lead_trail_empty_lines_=True).split("\n")
        out_file = os.path.join(self.get_scratch_space(), f"out.{file_ext}")
        dst_ext = "png"
        cache_file = os.path.join(self.get_scratch_space(), "image_hash_cache.json")
        # Render images.
        out_lines = dshdreim._render_images(txt, out_file, dst_ext, dry_run=True,
                                            cache_file=cache_file)
        # Check output.
        act = "\n".join(out_lines)
        hdbg.dassert_ne(act, "")
        exp = hprint.dedent(exp)
        self.assert_equal(act, exp, remove_lead_trail_empty_lines=True)

    # ///////////////////////////////////////////////////////////////////////////

    def test1(self) -> None:
        """
        Check text without image code in a LaTeX file.
        """
        in_lines = r"""
        A
        B
        """
        file_ext = "tex"
        exp = in_lines
        self.helper(in_lines, file_ext, exp)

    def test2(self) -> None:
        """
        Check text without image code in a Markdown file.
        """
        in_lines = r"""
        A
        ```bash
        Alice --> Bob
        ```
        B
        """
        file_ext = "md"
        exp = in_lines
        self.helper(in_lines, file_ext, exp)

    # ///////////////////////////////////////////////////////////////////////////

    def test_plantuml1(self) -> None:
        """
        Check bare plantUML code in a Markdown file.
        """
        in_lines = r"""
        ```plantuml
        Alice --> Bob
        ```
        """
        file_ext = "md"
        exp = r"""
        [//]: # ( ```plantuml)
        [//]: # ( Alice --> Bob)
        [//]: # ( ```)
        ![](figs/out.1.png)
        """
        self.helper(in_lines, file_ext, exp)

    def test_plantuml2(self) -> None:
        """
        Check plantUML code within other text in a Markdown file.
        """
        in_lines = r"""
        A
        ```plantuml
        Alice --> Bob
        ```
        B
        """
        file_ext = "md"
        exp = r"""
        A
        [//]: # ( ```plantuml)
        [//]: # ( Alice --> Bob)
        [//]: # ( ```)
        ![](figs/out.1.png)
        B
        """
        self.helper(in_lines, file_ext, exp)

    def test_plantuml3(self) -> None:
        """
        Check plantUML code that is already correctly formatted in a Markdown
        file.
        """
        in_lines = r"""
        ```plantuml
        @startuml
        Alice --> Bob
        @enduml
        ```
        """
        file_ext = "md"
        exp = r"""
        [//]: # ( ```plantuml)
        [//]: # ( @startuml)
        [//]: # ( Alice --> Bob)
        [//]: # ( @enduml)
        [//]: # ( ```)
        ![](figs/out.1.png)
        """
        self.helper(in_lines, file_ext, exp)

    def test_plantuml4(self) -> None:
        """
        Check bare plantUML code in a LaTeX file.
        """
        in_lines = r"""
        ```plantuml
        Alice --> Bob
        ```
        """
        file_ext = "tex"
        exp = r"""
        % ```plantuml
        % Alice --> Bob
        % ```
        \begin{figure} \includegraphics[width=\linewidth]{figs/out.1.png} \end{figure}
        """
        self.helper(in_lines, file_ext, exp)

    def test_plantuml5(self) -> None:
        """
        Check plantUML code within other text in a LaTeX file.
        """
        in_lines = r"""
        A
        ```plantuml
        Alice --> Bob
        ```
        B
        """
        file_ext = "tex"
        exp = r"""
        A
        % ```plantuml
        % Alice --> Bob
        % ```
        \begin{figure} \includegraphics[width=\linewidth]{figs/out.1.png} \end{figure}
        B
        """
        self.helper(in_lines, file_ext, exp)

    def test_plantuml6(self) -> None:
        """
        Check plantUML code that is already correctly formatted in a LaTeX
        file.
        """
        in_lines = r"""
        ```plantuml
        @startuml
        Alice --> Bob
        @enduml
        ```
        """
        file_ext = "tex"
        exp = r"""
        % ```plantuml
        % @startuml
        % Alice --> Bob
        % @enduml
        % ```
        \begin{figure} \includegraphics[width=\linewidth]{figs/out.1.png} \end{figure}
        """
        self.helper(in_lines, file_ext, exp)

    # ///////////////////////////////////////////////////////////////////////////

    def test_mermaid1(self) -> None:
        """
        Check bare mermaid code in a Markdown file.
        """
        in_lines = r"""
        ```mermaid
        flowchart TD;
          A[Start] --> B[End];
        ```
        """
        file_ext = "md"
        exp = r"""
        [//]: # ( ```mermaid)
        [//]: # ( flowchart TD;)
        [//]: # (   A[Start] --> B[End];)
        [//]: # ( ```)
        ![](figs/out.1.png)
        """
        self.helper(in_lines, file_ext, exp)

    def test_mermaid2(self) -> None:
        """
        Check mermaid code within other text in a Markdown file.
        """
        in_lines = r"""
        A
        ```mermaid
        flowchart TD;
          A[Start] --> B[End];
        ```
        B
        """
        file_ext = "md"
        exp = r"""
        A
        [//]: # ( ```mermaid)
        [//]: # ( flowchart TD;)
        [//]: # (   A[Start] --> B[End];)
        [//]: # ( ```)
        ![](figs/out.1.png)
        B
        """
        self.helper(in_lines, file_ext, exp)

    def test_mermaid3(self) -> None:
        """
        Check bare mermaid code in a LaTeX file.
        """
        in_lines = r"""
        ```mermaid
        flowchart TD;
          A[Start] --> B[End];
        ```
        """
        file_ext = "tex"
        exp = r"""

        % ```mermaid
        % flowchart TD;
        %   A[Start] --> B[End];
        % ```
        \begin{figure} \includegraphics[width=\linewidth]{figs/out.1.png} \end{figure}
        """
        self.helper(in_lines, file_ext, exp)

    def test_mermaid4(self) -> None:
        """
        Check mermaid code within other text in a LaTeX file.
        """
        in_lines = r"""
        A
        ```mermaid
        flowchart TD;
          A[Start] --> B[End];
        ```
        B
        """
        file_ext = "tex"
        exp = r"""
        A
        % ```mermaid
        % flowchart TD;
        %   A[Start] --> B[End];
        % ```
        \begin{figure} \includegraphics[width=\linewidth]{figs/out.1.png} \end{figure}
        B
        """
        self.helper(in_lines, file_ext, exp)

    def test_mermaid5(self) -> None:
        """
        Check mermaid code within other text in a md file.
        """
        in_lines = r"""
        A

        ```mermaid
        flowchart TD;
          A[Start] --> B[End];
        ```


        B
        """
        file_ext = "txt"
        exp = r"""
        A

        // ```mermaid
        // flowchart TD;
        //   A[Start] --> B[End];
        // ```
        ![](figs/out.1.png)


        B
        """
        self.helper(in_lines, file_ext, exp)

    def test_mermaid6(self) -> None:
        """
        Check mermaid code within other text in a md file.
        """
        in_lines = r"""
        A
        ```mermaid(hello_world.png)
        flowchart TD;
          A[Start] --> B[End];
        ```

        B
        """
        file_ext = "txt"
        exp = r"""
        A
        // ```mermaid(hello_world.png)
        // flowchart TD;
        //   A[Start] --> B[End];
        // ```
        ![](hello_world.png)

        B
        """
        self.helper(in_lines, file_ext, exp)

    def test_mermaid7(self) -> None:
        """
        Check commented mermaid code with an updated output file.
        """
        in_lines = r"""
        A
        // ```mermaid(hello_world2.png)
        // flowchart TD;
        // ```
        ![](hello_world.png)
        B
        """
        file_ext = "txt"
        exp = r"""
        A
        // ```mermaid(hello_world2.png)
        // flowchart TD;
        // ```
        ![](hello_world2.png)
        B
        """
        self.helper(in_lines, file_ext, exp)


# #############################################################################
# Test_render_images2
# #############################################################################


@pytest.mark.skipif(
    hserver.is_inside_ci(), reason="Disabled because of CmampTask10710"
)
class Test_render_images2(hunitest.TestCase):

    def helper(self, file_name: str) -> None:
        """
        Helper function to test rendering images from a file.
        """
        # Define input variables.
        in_file = os.path.join(self.get_input_dir(), file_name)
        in_lines = hio.from_file(in_file).split("\n")
        out_file = os.path.join(self.get_scratch_space(), file_name)
        dst_ext = "png"
        dry_run = True
        cache_file = os.path.join(self.get_scratch_space(), "image_hash_cache.json")
        # Call function to test.
        out_lines = dshdreim._render_images(
            in_lines,
            out_file,
            dst_ext,
            dry_run=dry_run,
            cache_file=cache_file
        )
        act = "\n".join(out_lines)
        # Check output.
        self.check_string(act)

    def test1(self) -> None:
        """
        Test running on a real Markdown file with plantUML code.
        """
        self.helper("im_architecture.md")

    def test2(self) -> None:
        """
        Test running on a real Markdown file with mermaid code.
        """
        self.helper("runnable_repo.md")

    def test3(self) -> None:
        """
        Test running on a full LaTeX file with plantUML code.
        """
        self.helper("sample_file_plantuml.tex")

    def test4(self) -> None:
        """
        Test running on a full LaTeX file with mermaid code.
        """
        self.helper("sample_file_mermaid.tex")
