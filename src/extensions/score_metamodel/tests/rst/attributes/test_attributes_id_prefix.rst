..
   # *******************************************************************************
   # Copyright (c) 2025 Contributors to the Eclipse Foundation
   #
   # See the NOTICE file(s) distributed with this work for additional
   # information regarding copyright ownership.
   #
   # This program and the accompanying materials are made available under the
   # terms of the Apache License Version 2.0 which is available at
   # https://www.apache.org/licenses/LICENSE-2.0
   #
   # SPDX-License-Identifier: Apache-2.0
   # *******************************************************************************
#CHECK: check_options


.. Neep with 2 ID parts tests
#EXPECT: wf__login__process.id (wf__login__process): does not follow pattern `^wf__[0-9a-z]+(?:_[0-9a-z]+)*$`.

.. workflow:: This is a test
   :id: wf__login__process

#EXPECT-NOT: wf__login.id (wf__login): does not follow pattern `^wf__[0-9a-z]+(?:_[0-9a-z]+)*$`.

.. workflow:: Valid workflow
   :id: wf__login


.. Neep with 3 ID parts tests
#EXPECT: feat_req__auth.id (feat_req__auth): does not follow pattern `^feat_req__[0-9a-z]+(?:_[0-9a-z]+)*__[0-9a-z]+(?:_[0-9a-z]+)*$`.

.. feat_req:: Invalid feature requirement
   :id: feat_req__auth

#EXPECT: feat_req__auth__validate__extra.id (feat_req__auth__validate__extra): does not follow pattern `^feat_req__[0-9a-z]+(?:_[0-9a-z]+)*__[0-9a-z]+(?:_[0-9a-z]+)*$`.

.. feat_req:: Invalid feature requirement
   :id: feat_req__auth__validate__extra

#EXPECT-NOT: feat_req__auth__validate.id (feat_req__auth__validate): does not follow pattern `^feat_req__[0-9a-z]+(?:_[0-9a-z]+)*__[0-9a-z]+(?:_[0-9a-z]+)*$`.

.. feat_req:: Valid feature requirement
   :id: feat_req__auth__validate
