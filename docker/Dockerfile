# Pinned (not ubuntu:latest): newer Ubuntu ships Python 3.14, on which pydantic's
# forward-ref evaluation breaks and langchain cannot define its models. 24.04 = 3.12.
FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive

RUN echo "==> Upgrading apk and installing system utilities ...." \
 && apt -y update \
 && apt-get install -y wget \
 && apt-get -y install sudo

RUN echo "==> Installing Python3 and pip ...." \  
 && apt-get install python3 -y \
 && apt install python3-pip -y

RUN echo "==> Install dos2unix..." \
  && sudo apt-get install dos2unix -y 

# Pin to the langchain 0.3 line: the app uses ConversationalRetrievalChain and
# ConversationBufferMemory, which were removed in langchain 1.x. --ignore-installed
# packaging keeps Debian's packaging in place (langchain-core 0.3 caps it <25).
RUN echo "==> Install langchain requirements.." \
  && pip install --break-system-packages --ignore-installed packaging --quiet \
       "langchain>=0.3,<0.4" "langchain-community>=0.3,<0.4" \
       "langchain-experimental>=0.3,<0.4" "langchain-openai>=0.2,<0.3" openai \
  && pip install --break-system-packages chromadb \
  && pip install --break-system-packages tiktoken

RUN echo "==> Install jq.." \
  && pip install --break-system-packages jq

RUN echo "==> Install streamlit.." \
  && pip install --break-system-packages streamlit --upgrade

# Install tshark
RUN apt-get update && apt-get install -y tshark

RUN echo "==> Adding pyshark ..." \
  && pip install --break-system-packages pyshark

RUN echo "==> Adding pandas ..." \
  && pip install --break-system-packages pandas

RUN echo "==> Adding scikit-learn ..." \
  && pip install --break-system-packages scikit-learn

RUN echo "==> Adding networkx ..." \
  && pip install --break-system-packages networkx

RUN echo "==> Adding pyvis ..." \
  && pip install --break-system-packages pyvis

# InstructorEmbedding only works with the old sentence-transformers 2.2.2, which
# imports huggingface_hub.cached_download (removed in hub 0.26). Pin the whole stack
# to a mutually compatible set; this is the last pip layer so nothing re-upgrades it.
RUN echo "==> Adding InstructorEmbedding ..." \
  && pip install --break-system-packages \
       "huggingface_hub==0.25.2" "transformers==4.44.2" \
       "sentence-transformers==2.2.2" InstructorEmbedding

COPY /packet_raptor /packet_raptor/
COPY /scripts /scripts/

RUN echo "==> Convert script..." \
  && dos2unix /scripts/startup.sh

CMD ["/bin/bash", "/scripts/startup.sh"]