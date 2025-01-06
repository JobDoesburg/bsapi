from abc import ABC, abstractmethod
import html
import re
import logging

logger = logging.getLogger(__name__)


def _group_paragraphs(feedback: str) -> list[list[str]]:
    paragraphs = []
    paragraph = []

    for line in feedback.splitlines():
        # Empty or blank lines mark the end of paragraphs.
        # Note that the line marking the end of a paragraph is not included in it.
        # Subsequent blank lines do cause empty paragraphs to be constructed, which is by design.
        if not line or line.isspace():
            paragraphs.append(paragraph)
            paragraph = []
        else:
            paragraph.append(line.strip())

    # The last paragraph does not need to end with a blank line.
    if paragraph:
        paragraphs.append(paragraph)

    return paragraphs


def _find_continue_point(feedback: str, i: int) -> int:
    # Continue after the next newline, unless we hit a non-whitespace character first.
    next_newline = feedback.find("\n", i)
    if feedback[i : next_newline + 1].isspace():
        return next_newline + 1
    else:
        return i + len(feedback[i:]) - len(feedback[i:].lstrip())


class FeedbackEncoder(ABC):
    """Base class to encode feedback text to HTML."""

    @abstractmethod
    def encode(self, feedback: str) -> str:
        """Encode the provided feedback text to HTML.

        :param feedback: The feedback text.
        :return: HTML string that can be set as the Brightspace HTML feedback.
        """
        pass


class HtmlEncoder(FeedbackEncoder):
    """Dummy class to pass through raw HTML."""

    def encode(self, feedback: str) -> str:
        """Encode the provided feedback HTML to HTML.

        :param feedback: The feedback HTML.
        :return: The unaltered feedback HTML string that can be set as the Brightspace HTML feedback.
        """
        return feedback


class BasicEncoder(FeedbackEncoder):
    """Basic plaintext to HTML encoder."""

    def encode(self, feedback: str) -> str:
        """Encode the provided feedback plaintext to HTML.
        The text is HTML escaped, and lines are merged into HTML paragraphs.
        Blank lines are used to delineate paragraphs, similar to Markdown.

        :param feedback: The feedback plaintext.
        :return: HTML string that can be set as the Brightspace HTML feedback.
        """
        escaped = html.escape(feedback.strip(), quote=False)
        paragraphs = [" ".join(paragraph) for paragraph in _group_paragraphs(escaped)]

        return "\n".join(f"<p>{paragraph}</p>" for paragraph in paragraphs)


class BasicCodeEncoder(FeedbackEncoder):
    """Basic plaintext to HTML encoder with support for Markdown style code blocks and inline code."""

    VALID_LANGUAGES = [
        "cpp",
        "csharp",
        "markup",
        "java",
        "javascript",
        "python",
        "arduino",
        "armasm",
        "bash",
        "c",
        "clike",
        "css",
        "haskell",
        "json",
        "kotlin",
        "latex",
        "matlab",
        "plain",
        "r",
        "racket",
        "regex",
        "sql",
        "wolfram",
    ]
    _INLINE_CODE_REGEX = r"`([^`\n]+)`"

    def __init__(
        self,
        default_language: str = "cpp",
        line_numbers: bool = True,
        dark_theme: bool = False,
    ):
        """Construct a new basic code-encoder instance.

        :param default_language: The default language to use in code blocks if no language was specified.
        :param line_numbers: Show line numbers in code blocks.
        :param dark_theme: Use dark theme in code blocks.
        """
        code_block_classes = ["d2l-code"]
        if dark_theme:
            code_block_classes.append("d2l-code-dark")
        if line_numbers:
            code_block_classes.append("line-numbers")
        self.code_block_class = " ".join(code_block_classes)
        self.default_language = default_language

    def _encode_codeblock(self, code: str) -> str:
        language, _, code = code.partition("\n")
        language = self.default_language if not language else language
        if language not in self.VALID_LANGUAGES:
            logger.warning(
                f'unknown code block language "{language}", considering it as code'
            )
            code = language + "\n" + code
            language = self.default_language

        return f'<pre class="{self.code_block_class}"><code class="language-{language}">{html.escape(code, quote=False)}</code></pre>'

    def _encode_plaintext(self, plaintext: str) -> str:
        escaped = html.escape(plaintext, quote=False)
        escaped = re.sub(self._INLINE_CODE_REGEX, r"<code>\1</code>", escaped)
        paragraphs = [" ".join(paragraph) for paragraph in _group_paragraphs(escaped)]

        return "\n".join(f"<p>{paragraph}</p>" for paragraph in paragraphs)

    def encode(self, feedback: str) -> str:
        """Encode the provided feedback plaintext to HTML.
        Text between triple backtick (```) characters is styled as code blocks, where the text immediately following the
        block opening, until a newline, is used as the language specifier.
        If no langauge is specified, the default is used.
        Regular text between single backticks, which may not span multiple lines, is styled as inline code.
        The text is HTML escaped, and lines are merged into HTML paragraphs.
        Blank lines are used to delineate paragraphs, similar to Markdown.

        :param feedback: The feedback plaintext.
        :return: HTML string that can be set as the Brightspace HTML feedback.
        """
        feedback = feedback.strip()
        output = ""
        i = 0

        while i < len(feedback):
            segment = feedback[i:]
            idx_code = segment.find("```")

            if idx_code == 0:
                # Code block start found at current feedback position.
                # Try to find closing index of the code block.
                idx_end = segment[3:].find("```")
                if idx_end == -1:
                    # Guard against unclosed code blocks by ignoring them.
                    logger.warning(
                        "unclosed code block, considering it as regular feedback"
                    )
                    output += self._encode_plaintext(segment)
                    i += len(segment)
                else:
                    # Found block end, so extract the contents and encode it.
                    output += self._encode_codeblock(segment[3 : idx_end + 3]) + "\n"
                    i = _find_continue_point(feedback, i + idx_end + 6)
            elif idx_code == -1:
                # No code block found, process feedback till the end.
                output += self._encode_plaintext(segment)
                i += len(segment)
            elif idx_code > 0:
                # Code block found later on, process feedback till the start of that block.
                output += self._encode_plaintext(segment[:idx_code]) + "\n"
                i += idx_code

        return output
