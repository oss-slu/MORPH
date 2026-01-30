FROM ros:humble AS runner
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync
RUN apt-get update && apt install -y ros-$ROS_DISTRO-foxglove-bridge
ENV PATH="/app/.venv/bin:$PATH"
COPY . .
RUN chmod +x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]