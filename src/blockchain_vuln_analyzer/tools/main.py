from typing import Callable, Coroutine, Any, Dict

class ToolProcessor:
    def __init__(
        self,
        runner: Callable[..., Coroutine[Any, Any, Dict]],
        formatter: Callable[[Dict, str], str],
        argument_extractor: Callable[[Dict | None], Dict],
    ):
        self.runner = runner
        self.formatter = formatter
        self.argument_extractor = argument_extractor

    async def process(self, arguments: Dict | None) -> tuple[Dict, Callable[[str], str]]:
        tool_args = self.argument_extractor(arguments or {})
        result = await self.runner(**tool_args)
        return result, lambda analysis_id: self.formatter(result, analysis_id) 