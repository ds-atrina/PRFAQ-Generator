import asyncio
from abc import ABC, abstractmethod
from typing import Any, Callable, Type, get_args, get_origin

from pydantic import (
    BaseModel as PydanticBaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class BaseTool(PydanticBaseModel, ABC):
    class _ArgsSchemaPlaceholder(PydanticBaseModel):
        pass

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    """Unique name of the tool."""
    description: str
    """How/when/why to use the tool."""
    args_schema: Type[PydanticBaseModel] = Field(
        default_factory=_ArgsSchemaPlaceholder, validate_default=True
    )
    """Schema for the arguments the tool accepts."""
    description_updated: bool = False
    """Flag to check if the description has been updated."""
    cache_function: Callable = lambda _args=None, _result=None: True
    """Function to determine if the tool should be cached; should return a boolean."""
    result_as_answer: bool = False
    """Flag to check if the tool should be the final agent answer."""
    max_usage_count: int | None = None
    """Maximum number of times this tool can be used. None = unlimited."""
    current_usage_count: int = 0
    """Current number of times this tool has been used."""

    @field_validator("args_schema", mode="before")
    @classmethod
    def _default_args_schema(
        cls, v: Type[PydanticBaseModel]
    ) -> Type[PydanticBaseModel]:
        if not isinstance(v, cls._ArgsSchemaPlaceholder):
            return v

        return type(
            f"{cls.__name__}Schema",
            (PydanticBaseModel,),
            {
                "__annotations__": {
                    k: v for k, v in cls._run.__annotations__.items() if k != "return"
                },
            },
        )

    @field_validator("max_usage_count", mode="before")
    @classmethod
    def validate_max_usage_count(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            raise ValueError("max_usage_count must be a positive integer")
        return v

    def model_post_init(self, __context: Any) -> None:
        self._generate_description()
        super().model_post_init(__context)

    def run(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        print(f"Using Tool: {self.name}")
        result = self._run(*args, **kwargs)

        # If _run is async, we safely run it
        if asyncio.iscoroutine(result):
            result = asyncio.run(result)

        self.current_usage_count += 1
        return result

    def reset_usage_count(self) -> None:
        """Reset the current usage count to zero."""
        self.current_usage_count = 0

    @abstractmethod
    def _run(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Actual implementation of the tool."""

    @classmethod
    def from_func(
        cls, func: Callable, name: str = None, description: str = None, **kwargs
    ) -> "BaseTool":
        """
        Create a Tool instance from a function.
        Args:
            func: function to wrap
            name: name to give the tool (defaults to func.__name__)
            description: description to use (defaults to func.__doc__)
            kwargs: any other BaseTool fields
        """
        if func.__doc__ is None:
            raise ValueError("Function must have a docstring")
        if func.__annotations__ is None:
            raise ValueError("Function must have type annotations")

        args_schema = type(
            (name or func.__name__).title() + "Schema",
            (PydanticBaseModel,),
            {
                "__annotations__": {
                    k: v for k, v in func.__annotations__.items() if k != "return"
                },
            },
        )

        return Tool(
            name=name or func.__name__,
            description=description or func.__doc__,
            func=func,
            args_schema=args_schema,
            **kwargs,
        )

    def _set_args_schema(self):
        if self.args_schema is None:
            class_name = f"{self.__class__.__name__}Schema"
            self.args_schema = type(
                class_name,
                (PydanticBaseModel,),
                {
                    "__annotations__": {
                        k: v
                        for k, v in self._run.__annotations__.items()
                        if k != "return"
                    },
                },
            )

    def _generate_description(self):
        args_schema = {
            name: {
                "description": field.description,
                "type": BaseTool._get_arg_annotations(field.annotation),
            }
            for name, field in self.args_schema.model_fields.items()
        }

        self.description = f"Tool Name: {self.name}\nTool Arguments: {args_schema}\nTool Description: {self.description}"

    @staticmethod
    def _get_arg_annotations(annotation: type[Any] | None) -> str:
        if annotation is None:
            return "None"

        origin = get_origin(annotation)
        args = get_args(annotation)

        if origin is None:
            return (
                annotation.__name__
                if hasattr(annotation, "__name__")
                else str(annotation)
            )

        if args:
            args_str = ", ".join(BaseTool._get_arg_annotations(arg) for arg in args)
            return f"{origin.__name__}[{args_str}]"

        return origin.__name__


class Tool(BaseTool):
    """Wraps a function as a Tool."""
    func: Callable

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        return self.func(*args, **kwargs)

    @classmethod
    def from_func(
        cls, func: Callable, name: str = None, description: str = None, **kwargs
    ) -> "Tool":
        return super().from_func(func, name, description, **kwargs)


def tool(
    *args,
    result_as_answer: bool = False,
    max_usage_count: int | None = None,
) -> Callable:
    """
    Decorator to create a tool from a function.

    Args:
        *args: either the function or the tool name as a string.
        result_as_answer: tool result is final agent answer.
        max_usage_count: max uses (None = unlimited).
    """

    def _make_with_name(tool_name: str) -> Callable:
        def _make_tool(f: Callable) -> BaseTool:
            return Tool.from_func(
                f,
                name=tool_name,
                result_as_answer=result_as_answer,
                max_usage_count=max_usage_count,
            )
        return _make_tool

    if len(args) == 1 and callable(args[0]):
        return _make_with_name(args[0].__name__)(args[0])
    if len(args) == 1 and isinstance(args[0], str):
        return _make_with_name(args[0])
    raise ValueError("Invalid arguments")