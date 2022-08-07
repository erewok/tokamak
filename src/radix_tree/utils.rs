use std::collections::BTreeMap;

pub enum ParamToken {
    LeftBrace,
    Colon,
    RightBrace,
    Star,
}

/// A single URL parameter, consisting of a key and a value.
#[derive(Debug, PartialEq, Eq, Ord, PartialOrd, Default, Copy, Clone)]
pub struct DynamicPathElement<'k, 'v> {
    pub key: &'k [u8],
    pub value: &'v [u8],
}

pub enum PathElement<'a> {
    Static(&'a [u8]),
    Dynamic(DynamicPathElement<'a, 'a>),
}

pub struct Path<'a, V> {
    context: BTreeMap<&'a [u8], V>,
    path: Vec<PathElement<'a>>,
}
